# lots of code from https://docs.qtile.org/en/latest/_modules/libqtile/widget/bluetooth.html
# Copyright (c) 2023 elParaguayo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

import asyncio
from functools import wraps
from typing import Callable
from dbus_next.aio import MessageBus, ProxyObject, ProxyInterface
from dbus_next import BusType
from dbus_next.errors import DBusError, InterfaceNotFoundError
from src.utils import Utils

BLUEZ_SERVICE = "org.bluez"
OBJECT_MANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

def _catch_dbus_error(f):
    """
    Decorator to catch DBusErrors and log a message.
    Modifies the function to return the error as string if it occurs
    """
    @wraps(f)
    async def async_wrapper(*args, **kwargs):    
        try:
            return await f(*args, **kwargs)
        except DBusError as err:
            Utils.log("DBusError: " + str(err))
            return str(err)
    return async_wrapper

class DeviceState(object):
    CONNECTED = "connected"
    PAIRED = "paired"
    UNPAIRED = "unpaired"

class BluetoothDevice(object):
    """
    Interface for a BT device in Bluez. 
    See https://github.com/bluez/bluez/blob/master/doc/org.bluez.Device.rst
    """
    BLUEZ_TYPE = "org.bluez.Device1"

    def __init__(self, interface: ProxyInterface, properties_interface: ProxyInterface, on_device_connected_callback: Callable, on_device_disconnected_callback: Callable) -> None:
        self.connected = False
        self.paired = False
        self.status = DeviceState.UNPAIRED
        self.interface = interface
        self.is_audio_sink = False
        self.properties = properties_interface
        self.on_device_connected_callback = on_device_connected_callback
        self.on_device_disconnected_callback = on_device_disconnected_callback
        self.media_control1: MediaControl1 = None

    def add_change_listeners(self):
        # note: this is called for changes in ALL interfaces, not just in this device!
        self.properties.on_properties_changed(self.properties_changed)

    @_catch_dbus_error
    async def properties_changed(self, interface_name:str=None, _changed_properties=None, _invalidated_properties=None) -> str | None:
        """Refresh all the properties for the device."""
        # Note: this might be a change for some other device, these are sent out globally :/
        print("BT device prop change " + str(interface_name) + " " + str(_changed_properties) + " " + str(_invalidated_properties))
        # Some devices don't report a name so we fall back to the device address
        try:
            self.name = await self.interface.get_name()
        except (AttributeError, DBusError):
            self.name = await self.interface.get_address()
        self.connected, self.paired, self.address, uuids = await asyncio.gather(
            self.interface.get_connected(),
            self.interface.get_paired(),
            self.interface.get_address(),
            self.interface.get_uui_ds()
        )
        # see https://www.bluetooth.com/wp-content/uploads/Files/Specification/Assigned_Numbers.pdf
        for uuid in uuids:
            if uuid[4:8].lower() == '110b': # audio sink profile
                self.is_audio_sink = True
                break
        new_status = DeviceState.UNPAIRED
        if self.connected:
            new_status = DeviceState.CONNECTED
        elif self.paired and not self.connected:
            new_status = DeviceState.PAIRED
        
        if interface_name and interface_name == BluetoothDevice.BLUEZ_TYPE and self.status != new_status:
            self.status = new_status
            if new_status == DeviceState.CONNECTED:
                Utils.log("BT device " + self.name + " connected")
                self.on_device_connected_callback()
            else:
                Utils.log("BT device " + self.name + " disconnected")
                self.on_device_disconnected_callback()
        self.status = new_status

    @_catch_dbus_error
    async def pair_connect_trust(self) -> str | None:
        """
        pair if needed and then connect and trust the device.
        Returns an error message if it did not succeed.
        """
        if self.paired:
            await self.interface.call_connect()
        else:
            await self.interface.call_pair()
            await self.interface.call_connect()
            await self.interface.set_trusted(True)
        return "connected to " + self.name

    @_catch_dbus_error
    async def disconnect(self) -> str | None:
        await self.interface.call_disconnect()
    
    def destructor():
        pass
        #self.properties.

class BluetoothAdapter(object):
    """
    Interface for a BT adapter in Bluez. 
    See https://github.com/bluez/bluez/blob/master/doc/org.bluez.Adapter.rst
    """
    BLUEZ_TYPE = "org.bluez.Adapter1"

    def __init__(self, interface, properties_interface) -> None:
        self.interface = interface
        self.discovering = False
        self.powered = False
        self.name = "undefined"
        self.properties = properties_interface
        # note: this is called for changes in ALL interfaces, not just in this device!
        self.properties.on_properties_changed(self.properties_changed)

    @_catch_dbus_error
    async def properties_changed(self, _interface_name=None, _changed_properties=None, _invalidated_properties=None) -> str | None:
        """Refresh all the properties for the device."""
        self.discovering = await self.interface.get_discovering()
        self.powered = await self.interface.get_powered()
        self.name = await self.interface.get_name()

    async def start_discovery(self):
        await self.interface.call_start_discovery()

    async def stop_discovery(self):
        await self.interface.call_stop_discovery()

class MediaControl1(object):
    """
    interface for querying and controlling BT media devices (e.g. volume)
    """
    BLUEZ_TYPE = "org.bluez.MediaControl1"
    def __init__(self, interface, properties_interface) -> None:
        self.interface = interface
        self.properties = properties_interface
        self.connected = False
        self.properties.on_properties_changed(self.properties_changed)

    @_catch_dbus_error
    async def properties_changed(self, _interface_name=None, _changed_properties=None, _invalidated_properties=None) -> str | None:
        """Refresh all the properties for the device."""
        self.connected = await self.interface.get_connected()
    
    async def volume_up(self):
        if self.connected:
            await self.interface.call_volume_up()

    async def volume_down(self):
        if self.connected:
            await self.interface.call_volume_down()

class BluetoothManager(object):

    def __init__(self, on_device_connected_callback: Callable, on_device_disconnected_callback: Callable) -> None:
        self.on_device_connected_callback = on_device_connected_callback
        self.on_device_disconnected_callback = on_device_disconnected_callback
        self.initialized = False
        self.devs: dict[str, BluetoothDevice] = {}
        self.adapter: BluetoothAdapter | None = None

    @_catch_dbus_error
    async def init_async(self) -> str | None:
        if self.initialized:
            raise Exception("Tried to init BT manager twice")
        self.initialized = True
        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        proxy = await self.get_proxy('/')
        self.objectmanager_interface = proxy.get_interface(OBJECT_MANAGER_INTERFACE)
        await self.__get_devices()

    @_catch_dbus_error
    async def get_proxy(self, path) -> str | ProxyObject:
        """Provides proxy object after introspecting the given path."""
        device_introspection = await self.bus.introspect(BLUEZ_SERVICE, path)
        proxy = self.bus.get_proxy_object(BLUEZ_SERVICE, path, device_introspection)
        return proxy

    @_catch_dbus_error
    async def scan_for_devices(self, time_in_secs: float) -> str | None:
        """Scans for devices for the given time and populates the 'devs' array with the results"""
        print("scanning for devices")
        await self.adapter.start_discovery()
        await asyncio.sleep(time_in_secs)
        await self.__get_devices()
        await self.adapter.stop_discovery()
    
    def scan_for_devices_callback(self, callback: Callable[[str | None], None], time_in_secs: float):
        """
        Same as scan_for_devices just with a callback
        `callback` is a function, that accepts one `str` argument, it has a value if there was an error
        """
        self.scan_task = set()
        task = asyncio.create_task(self.scan_for_devices(time_in_secs=time_in_secs))
        # Add task to the set. This creates a strong reference.
        self.scan_task.add(task)
        def done_callback(task):
            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            self.scan_task.discard(task)
            callback(task.result())
        task.add_done_callback(done_callback)

    async def __get_devices(self):
        """
        Retrieve list of managed objects.

        These are devices/interfaces that have previously been paired but may or may
        not currently be connected.

        Additionally, if the device is scanning, available objects will also
        appear here, albeit temporarily.
        """
        objects = await self.objectmanager_interface.call_get_managed_objects()
        for path, interfaces in objects.items(): # path looks like '/org/bluez/hci0/dev_MA_CA_DD_RE_SS_12' or '/org/bluez'
            proxy = await self.get_proxy(path)
            # instead of classes, just emit signals? since BT device list is changing we cant know for sure
            # that the same object is associated with a reconnected device
            for interface_name in interfaces:
                try:
                    interface = proxy.get_interface(interface_name)
                    properties = proxy.get_interface(PROPERTIES_INTERFACE)
                except InterfaceNotFoundError as err:
                    # not an error, printed when some capability is not supported(?)
                    continue
                # it would be much nicer to pass a properties object that reacts only to changes in the given device_type
                if interface_name == BluetoothDevice.BLUEZ_TYPE and (path not in self.devs):
                    bt_dev = BluetoothDevice(interface, properties, self.on_device_connected_callback, self.on_device_disconnected_callback)
                    await bt_dev.properties_changed()
                    if bt_dev.is_audio_sink == True:
                        bt_dev.add_change_listeners()
                        # look for a media control interface for this device
                        for device_type2 in interfaces:
                            if device_type2 == MediaControl1.BLUEZ_TYPE:
                                # note: This type is deprecated, but JBL Flip 5 does not list the new "org.bluez.MediaPlayer1"
                                interface2 = proxy.get_interface(device_type2)
                                bt_dev.media_control1 = MediaControl1(interface2, properties)
                                await bt_dev.media_control1.properties_changed()
                        Utils.log("BT DEV '" + bt_dev.name + "' ADDED TO " + path)
                        self.devs[path] = bt_dev
                elif interface_name == BluetoothAdapter.BLUEZ_TYPE:
                    self.adapter = BluetoothAdapter(interface, properties)
                    await self.adapter.properties_changed()
    
    def get_connected_device(self) -> BluetoothDevice | None:
        if self.devs == None:
            return None
        for path, dev in self.devs.items():
            if dev.connected == True:
                return dev
        return None
