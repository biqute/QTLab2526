from abc import ABC, abstractmethod
import inspect

class Instrument(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def initialize(self):
        """Initialize the instrument."""
        pass

    @abstractmethod
    def info(self, verbose=False):
        """Get information about the instrument."""
        pass

    @abstractmethod
    def _activate(self):
        """Activate the instrument. Put it in remote mode."""
        pass

    def available_acquisition_methods(self) -> dict:
        """Return dictionary of available acquisition methods with their parameters."""
        methods_dict = {}
        for method_name in dir(self):
            if callable(getattr(self, method_name)) and method_name.startswith("acq_"):
                method = getattr(self, method_name)
                params = inspect.signature(method).parameters
                # Convert parameters to a list, excluding 'self'
                param_list = [name for name in params.keys() if name != 'self']
                methods_dict[method_name] = param_list
        return methods_dict

    def has_acquisition(self) -> bool:
        """Check if any acquisition methods exist."""
        return len(self.available_acquisition_methods()) > 0

    @abstractmethod
    def reset(self):
        """Reset the instrument."""
        pass

    @abstractmethod
    def close_connection(self):
        """Disconnect the instrument."""
        pass
    
    @abstractmethod
    def shutdown(self):
        """Shut down the instrument."""
        pass
    
    @abstractmethod
    def kill(self):
        """Kill the instrument."""
        pass