from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.image import Image
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.bluetooth import BluetoothClient, BluetoothDevice
import modules.icons as icons

class BluetoothDeviceSlot(CenterBox):
    def __init__(self, device: BluetoothDevice, **kwargs):
        super().__init__(name="bluetooth-device", **kwargs)
        self.device = device
        self.device.connect("changed", self.on_changed)
        self.device.connect(
            "notify::closed", lambda *_: self.device.closed and self.destroy()
        )

        self.connection_label = Label(name="bluetooth-connection", markup=icons.bluetooth_disconnected)
        self.connect_button = Button(
            name="bluetooth-connect",
            label="Connect",
            on_clicked=lambda *_: self.device.set_connecting(not self.device.connected),
        )

        self.start_children = [
            Box(
                spacing=8,
                children=[
                    Image(icon_name=device.icon_name + "-symbolic", size=32),
                    Label(label=device.name),
                    self.connection_label,
                ],
            )
        ]
        self.end_children = self.connect_button

        self.device.emit("changed")  # to update display status

    def on_changed(self, *_):
        self.connection_label.set_markup(
            icons.bluetooth_connected if self.device.connected else icons.bluetooth_disconnected
        )
        if self.device.connecting:
            self.connect_button.set_label(
                "Connecting..." if not self.device.connecting else "Disconnecting..."
            )
        else:
            self.connect_button.set_label(
                "Connect" if not self.device.connected else "Disconnect"
            )
        return


class BluetoothConnections(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="bluetooth",
            spacing=8,
            orientation="vertical",
            **kwargs,
        )

        self.client = BluetoothClient(on_device_added=self.on_device_added)
        self.scan_button = Button(name="bluetooth-scan", label="Scan", on_clicked=lambda *_: self.client.toggle_scan())
        self.toggle_button = Button(name="bluetooth-toggle", label="OFF", on_clicked=lambda *_: self.client.toggle_power())

        self.client.connect(
            "notify::enabled",
            lambda *_: self.toggle_button.set_label(
                "Enabled" if self.client.enabled else "Disabled"
            ),
        )
        self.client.connect(
            "notify::scanning",
            lambda *_: self.scan_button.set_label(
                "Stop" if self.client.scanning else "Scan"
            ),
        )

        self.paired_box = Box(spacing=2, orientation="vertical")
        self.available_box = Box(spacing=2, orientation="vertical")

        self.children = [
            CenterBox(start_children=self.scan_button, center_children=Label(name="bluetooth-text", label="Bluetooth Devices"), end_children=self.toggle_button),
            Label(name="bluetooth-text", label="Paired"),
            ScrolledWindow(min_content_size=(-1, -1), child=self.paired_box),
            Label(name="bluetooth-text", label="Available"),
            ScrolledWindow(min_content_size=(-1, -1), child=self.available_box),
        ]

        # to run notify closures thus display the status
        # without having to wait until an actual change
        self.client.notify("scanning")
        self.client.notify("enabled")

    def on_device_added(self, client: BluetoothClient, address: str):
        if not (device := client.get_device(address)):
            return
        slot = BluetoothDeviceSlot(device)

        if device.paired:
            return self.paired_box.add(slot)
        return self.available_box.add(slot)
