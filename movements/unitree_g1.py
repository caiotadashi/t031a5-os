import time
import sys
from dataclasses import dataclass
from typing import Dict, Optional
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient, action_map

class UnitreeG1Movement:
    def __init__(self, network_interface: str = "eth0"):
        """
        Initialize the Unitree G1 movement handler.
        
        Args:
            network_interface: Network interface to use for communication (default: "eth0")
        """
        # Initialize channel factory
        ChannelFactoryInitialize(0, network_interface)
        
        # Initialize arm action client
        self.arm_client = G1ArmActionClient()
        self.arm_client.Init()
        self.arm_client.SetTimeout(10.0)
        
        # Map movement names to action names
        self.movement_map = {
            "release_arm": "release arm",
            "shake_hand": "shake hand",
            "high_five": "high five",
            "hug": "hug",
            "high_wave": "high wave",
            "clap": "clap",
            "face_wave": "face wave",
            "left_kiss": "left kiss",
            "heart": "heart",
            "right_heart": "right heart",
            "hands_up": "hands up",
            "x_ray": "x-ray",
            "right_hand_up": "right hand up",
            "reject": "reject",
            "right_kiss": "right kiss",
            "two_hand_kiss": "two-hand kiss"
        }
    
    def execute_movement(self, movement_name: str) -> bool:
        """
        Execute a predefined movement by name.
        
        Args:
            movement_name: Name of the movement to execute (e.g., "wave", "hug")
            
        Returns:
            bool: True if movement was executed successfully, False otherwise
        """
        # Convert movement name to lowercase and replace spaces with underscores
        normalized_name = movement_name.lower().replace(" ", "_")
        
        if normalized_name not in self.movement_map:
            print(f"Error: Unknown movement '{movement_name}'. Available movements: {list(self.movement_map.keys())}")
            return False
        
        action_name = self.movement_map[normalized_name]
        print(f"Executing movement: {action_name}")
        
        try:
            # Execute the movement using action_map
            self.arm_client.ExecuteAction(action_map.get(action_name))
            return True
        except Exception as e:
            print(f"Error executing movement '{movement_name}': {str(e)}")
            return False
    
    def get_available_movements(self) -> Dict[str, str]:
        """
        Get a dictionary of all available movements and their action names.
        
        Returns:
            Dict[str, str]: Mapping of movement names to their action names
        """
        return self.movement_map.copy()

# Example usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} network_interface [movement_name]")
        print("\nAvailable movements:")
        for name, action in UnitreeG1Movement().get_available_movements().items():
            print(f"- {name} (Action: '{action}')")
        sys.exit(1)
    
    try:
        # Initialize the movement handler
        movement_handler = UnitreeG1Movement(sys.argv[1])
        
        # Get movement from command line or default to "wave"
        movement = sys.argv[2] if len(sys.argv) > 2 else "wave"
        
        print(f"Attempting to execute movement: {movement}")
        success = movement_handler.execute_movement(movement)
        
        if success:
            print(f"Successfully executed movement: {movement}")
        else:
            print(f"Failed to execute movement: {movement}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)