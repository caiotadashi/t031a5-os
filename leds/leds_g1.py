import time
import sys
from dataclasses import dataclass
from typing import Tuple, Optional
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.audio.g1_audio_client import AudioClient

class UnitreeG1LEDs:
    def __init__(self, network_interface: str = "eth0"):
        """
        Initialize the Unitree G1 LED controller.
        
        Args:
            network_interface: Network interface to use for communication (default: "eth0")
        """
        # Initialize channel factory
        ChannelFactoryInitialize(0, network_interface)
        
        # Initialize audio client (which includes LED control)
        self.audio_client = AudioClient()
        self.audio_client.Init()
        self.audio_client.SetTimeout(10.0)
        
        # Define color presets (RGB values 0-255)
        self.color_presets = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "white": (255, 255, 255),
            "off": (0, 0, 0)
        }
    
    def set_color(self, red: int, green: int, blue: int) -> bool:
        """
        Set the LED color using RGB values.
        
        Args:
            red: Red component (0-255)
            green: Green component (0-255)
            blue: Blue component (0-255)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input values
            for value in [red, green, blue]:
                if not 0 <= value <= 255:
                    print(f"Error: RGB values must be between 0 and 255. Got: {red}, {green}, {blue}")
                    return False
            
            self.audio_client.LedControl(red, green, blue)
            return True
        except Exception as e:
            print(f"Error setting LED color: {e}")
            return False
    
    def set_preset_color(self, color_name: str) -> bool:
        """
        Set the LED color using a preset name.
        
        Args:
            color_name: Name of the preset color (e.g., "red", "green", "blue")
            
        Returns:
            bool: True if successful, False otherwise
        """
        color_name = color_name.lower()
        if color_name not in self.color_presets:
            print(f"Error: Unknown color preset '{color_name}'. Available presets: {', '.join(self.color_presets.keys())}")
            return False
            
        red, green, blue = self.color_presets[color_name]
        return self.set_color(red, green, blue)
    
    def blink(self, color_name: str, times: int = 3, interval: float = 0.5) -> bool:
        """
        Blink the LED with a specified color.
        
        Args:
            color_name: Name of the color to blink
            times: Number of times to blink
            interval: Time in seconds between blinks
            
        Returns:
            bool: True if successful, False otherwise
        """
        if color_name.lower() not in self.color_presets:
            print(f"Error: Unknown color preset '{color_name}'")
            return False
            
        red, green, blue = self.color_presets[color_name.lower()]
        
        try:
            for _ in range(times):
                self.audio_client.LedControl(red, green, blue)
                time.sleep(interval)
                self.audio_client.LedControl(0, 0, 0)
                time.sleep(interval)
            return True
        except Exception as e:
            print(f"Error during LED blink: {e}")
            return False

# Example usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} network_interface [color_name|r g b]")
        print("Examples:")
        print(f"  {sys.argv[0]} eth0 red")
        print(f"  {sys.argv[0]} eth0 255 0 0")
        print("\nAvailable color presets:", ", ".join(UnitreeG1LEDs().color_presets.keys()))
        sys.exit(1)
    
    led_controller = UnitreeG1LEDs(sys.argv[1])
    
    try:
        if len(sys.argv) == 3:
            # Set preset color
            color_name = sys.argv[2]
            if led_controller.set_preset_color(color_name):
                print(f"LED set to {color_name}")
        elif len(sys.argv) == 5 and sys.argv[2].isdigit() and sys.argv[3].isdigit() and sys.argv[4].isdigit():
            # Set custom RGB color
            r, g, b = map(int, sys.argv[2:5])
            if led_controller.set_color(r, g, b):
                print(f"LED set to RGB({r}, {g}, {b})")
        else:
            print("Invalid arguments. Use either a preset color name or RGB values.")
    except KeyboardInterrupt:
        print("\nTurning off LED...")
        led_controller.set_color(0, 0, 0)
        sys.exit(0)
