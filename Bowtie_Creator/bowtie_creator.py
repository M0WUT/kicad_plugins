from dataclasses import dataclass
from enum import Enum, auto
from time import sleep
from typing import Optional

import pcbnew


class KicadLayer(Enum):
    TOP = auto()
    L2 = auto()
    L3 = auto()
    L4 = auto()
    L5 = auto()
    L6 = auto()
    L7 = auto()
    L8 = auto()
    L9 = auto()
    BOTTOM = auto()

    def get_layer_code(self) -> int:
        layer_codes = {
            KicadLayer.TOP: pcbnew.F_Cu,
            KicadLayer.L2: pcbnew.In1_Cu,
            KicadLayer.L3: pcbnew.In2_Cu,
            KicadLayer.L4: pcbnew.In3_Cu,
            KicadLayer.L5: pcbnew.In4_Cu,
            KicadLayer.L6: pcbnew.In5_Cu,
            KicadLayer.L7: pcbnew.In6_Cu,
            KicadLayer.L8: pcbnew.In7_Cu,
            KicadLayer.L9: pcbnew.In8_Cu,
            KicadLayer.BOTTOM: pcbnew.B_Cu,
        }
        return layer_codes[self]


class Net:
    def __init__(self, net_name: str, net_code: int):
        self._net_name = net_name
        self._net_code = net_code

    def __repr__(self):
        return f"{self._net_name} (Code: {self._net_code})"

    def get_net_code(self) -> int:
        return self._net_code


class Component:
    def __init__(self, footprint: pcbnew.FOOTPRINT):
        self.footprint = footprint

    def set_position(
        self,
        x_pos_mm: float,
        y_pos_mm: float,
        layer: KicadLayer,
        rotation_deg: Optional[float] = None,
    ):

        assert layer in [
            KicadLayer.TOP,
            KicadLayer.BOTTOM,
        ], "Components can only be assigned to top or bottom layer"

        self.footprint.SetLayerAndFlip(layer.get_layer_code())

        self.footprint.SetX(pcbnew.FromMM(x_pos_mm))
        self.footprint.SetY(pcbnew.FromMM(y_pos_mm))
        if rotation_deg is not None:
            # Function requires angle to be 0 <= angle < 360
            self.footprint.SetOrientationDegrees((rotation_deg + 360) % 360)

    def _set_reference_visible_state(self, visible: bool):
        self.footprint.Reference().SetVisible(visible)

    def show_reference(self):
        self._set_reference_visible_state(True)

    def hide_reference(self):
        self._set_reference_visible_state(False)


NUM_COLS = 21
START_COLUMN_SIZE = 28

# Coordinates of Start LED (first one on bottom left on left side of bowtie)
START_X = 93.25
CENTRE_LINE_Y = 100

COLUMN_SPACING = 2.25  # mm
ROW_SPACING = 2.25  # mm

VIA_DIAMETER = 0.45
VIA_HOLE = 0.2

LED_PAD_OFFSET_X = 0.515
LED_PAD_OFFSET_Y = 0.43


@dataclass
class M0WUTPcbHandler:

    pcb: pcbnew.BOARD
    default_via_hole_mm: float = 0.45
    default_via_pad_mm: float = 0.45
    default_track_width_mm: float = 0.2

    # Function used from https://jeffmcbride.net/kicad-track-layout/
    @classmethod
    def _pcbpoint(cls, x: float, y: float) -> pcbnew.VECTOR2I:
        return pcbnew.VECTOR2I(int(pcbnew.FromMM(x)), int(pcbnew.FromMM(y)))

    def add_via(
        self,
        x_pos_mm: float,
        y_pos_mm: float,
        net: Net,
        hole_diameter_mm: Optional[float] = None,
        pad_diameter_mm: Optional[float] = None,
    ):
        new_via = pcbnew.PCB_VIA(self.pcb)

        new_via.SetX(pcbnew.FromMM(x_pos_mm))
        new_via.SetY(pcbnew.FromMM(y_pos_mm))
        new_via.SetDrill(
            pcbnew.FromMM(
                hole_diameter_mm
                if hole_diameter_mm is not None
                else self.default_via_hole_mm
            )
        )
        new_via.SetWidth(
            pcbnew.FromMM(
                pad_diameter_mm
                if pad_diameter_mm is not None
                else self.default_via_pad_mm
            )
        )
        self.pcb.Add(new_via)
        new_via.SetNetCode(net.get_net_code())

    def add_track(
        self,
        start_x_mm: float,
        start_y_mm: float,
        end_x_mm: float,
        end_y_mm: float,
        net: Net,
        layer: KicadLayer,
        width_mm: Optional[float] = None,
    ):

        new_track = pcbnew.PCB_TRACK(self.pcb)

        new_track.SetStartEnd(
            M0WUTPcbHandler._pcbpoint(start_x_mm, start_y_mm),
            M0WUTPcbHandler._pcbpoint(end_x_mm, end_y_mm),
        )
        new_track.SetWidth(
            pcbnew.FromMM(width_mm)
            if width_mm is not None
            else pcbnew.FromMM(self.default_track_width_mm)
        )
        new_track.SetLayer(layer.get_layer_code())
        self.pcb.Add(new_track)
        new_track.SetNetCode(net.get_net_code())

    def add_multipoint_track(
        self,
        points: list[tuple[float, float]],
        net: Net,
        layer: KicadLayer,
        width: Optional[float] = None,
    ):
        for index in range(len(points) - 1):
            start_x = points[index][0]
            start_y = points[index][1]
            end_x = points[index + 1][0]
            end_y = points[index + 1][1]
            self.add_track(start_x, start_y, end_x, end_y, net, layer, width)

    def get_component(self, component_reference: str) -> Optional[Component]:
        x = self.pcb.FindFootprintByReference(component_reference)
        if x:
            return Component(x)
        else:
            return None

    def delete_all_tracks(self) -> None:
        tracks = self.pcb.GetTracks()
        for t in tracks:
            # This "helpfully returns all Tracks and Vias"
            if t.GetClass() == "PCB_TRACK":
                self.pcb.Delete(t)
        sleep(1)
        pcbnew.Refresh()
        sleep(1)

    def delete_all_vias(self) -> None:
        tracks = self.pcb.GetTracks()
        for t in tracks:
            if t.GetClass() == "PCB_VIA":
                self.pcb.Remove(t)
        pcbnew.Refresh()

    def delete_all_tracks_and_vias(self) -> None:
        tracks = self.pcb.GetTracks()
        for t in tracks:
            self.pcb.Remove(t)
        pcbnew.Refresh()

    def get_net(self, net_name: str) -> Optional[Net]:
        x = self.pcb.FindNet(net_name)
        if x:
            return Net(net_name, x.GetNetCode())
        else:
            return None


def create_bowtie(kicad_pcb: pcbnew.BOARD):

    pcb = M0WUTPcbHandler(
        pcb=kicad_pcb,
        default_via_hole_mm=0.2,
        default_via_pad_mm=VIA_DIAMETER,
        default_track_width_mm=VIA_HOLE,
    )

    net_5v = pcb.get_net("5V0")
    assert net_5v is not None
    net_0v = pcb.get_net("0V")
    assert net_0v is not None

    # Wipe board from previous attempts
    pcb.delete_all_tracks_and_vias()

    # Setup orientation conditions
    current_led_reference = 1
    leds_per_column = START_COLUMN_SIZE
    add_led_next_column = False

    flip = False
    for col in range(NUM_COLS):
        led_centre_x = START_X + COLUMN_SPACING * col
        for row in range(leds_per_column):
            led = pcb.get_component(f"LD{current_led_reference}")
            # cap = pcb.get_component(f"C{current_led_reference}")
            assert led is not None, f"Couldn't find LD{current_led_reference}"
            # assert cap is not None, f"Couldn't find C{current_led_reference}"

            led_centre_y = (
                CENTRE_LINE_Y
                - row * ROW_SPACING
                + 0.5 * (leds_per_column - 1) * ROW_SPACING
            )

            led.set_position(
                led_centre_x,
                led_centre_y,
                KicadLayer.TOP,
                rotation_deg=0,
            )
            led.hide_reference()

            # Bottom left via i.e. negative X, positive Y
            # This goes to a via
            x_pos = led_centre_x - LED_PAD_OFFSET_X
            y_pos = led_centre_y + LED_PAD_OFFSET_Y
            pcb.add_track(
                x_pos,
                y_pos,
                x_pos,
                led_centre_y + 0.5 * ROW_SPACING,
                net_5v,
                KicadLayer.TOP,
                0.127,
            )
            pcb.add_via(
                x_pos,
                led_centre_y + 0.5 * ROW_SPACING,
                net_5v,
                VIA_HOLE,
                VIA_DIAMETER,
            )
            pcb.add_track(
                x_pos,
                led_centre_y + 0.5 * ROW_SPACING,
                x_pos + COLUMN_SPACING,
                led_centre_y + 0.5 * ROW_SPACING,
                net_5v,
                KicadLayer.L3,
                0.45,
            )

            if row > 0:

                # Top right via i.e. positive X, negative Y (becauese Kicad)
                # This goes down and to the left
                x_pos = led_centre_x + LED_PAD_OFFSET_X
                y_pos = led_centre_y - LED_PAD_OFFSET_Y
                pcb.add_multipoint_track(
                    [
                        (x_pos, y_pos),
                        (x_pos - 0.435, y_pos + 0.435),
                        (
                            x_pos - 0.435,
                            y_pos + ROW_SPACING - 0.435,
                        ),
                        (x_pos, y_pos + ROW_SPACING),
                    ],
                    net_5v,
                    KicadLayer.TOP,
                    0.127,
                )
                # Top left via i.e. negative X, negative Y
                # This goes down and to the left
                x_pos = led_centre_x - LED_PAD_OFFSET_X
                y_pos = led_centre_y - LED_PAD_OFFSET_Y
                pcb.add_multipoint_track(
                    [
                        (x_pos, y_pos),
                        (x_pos - 0.435, y_pos + 0.435),
                        (
                            x_pos - 0.435,
                            y_pos + ROW_SPACING - 0.435,
                        ),
                        (x_pos, y_pos + ROW_SPACING),
                    ],
                    net_5v,
                    KicadLayer.TOP,
                    0.127,
                )

                # # Bottom right via i.e. positive X, positive Y
                # # This goes down and right
                x_pos = led_centre_x + LED_PAD_OFFSET_X
                y_pos = led_centre_y + LED_PAD_OFFSET_Y
                pcb.add_multipoint_track(
                    [
                        (x_pos, y_pos),
                        (x_pos + 0.435, y_pos + 0.435),
                        (
                            x_pos + 0.435,
                            y_pos + ROW_SPACING - 0.435,
                        ),
                        (x_pos, y_pos + ROW_SPACING),
                    ],
                    net_5v,
                    KicadLayer.TOP,
                    0.127,
                )

            current_led_reference += 1

        if add_led_next_column == (2 if flip else 1):
            leds_per_column -= 2
            add_led_next_column = 0
            flip = not flip
        else:
            add_led_next_column = add_led_next_column + 1

    pcbnew.Refresh()
