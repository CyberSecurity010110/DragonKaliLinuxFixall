from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os

# Initialize LLM
llm = ChatOpenAI(temperature=0)

# Create base class for modules
class RepairModule:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.memory = ConversationBufferMemory()
        
    def scan(self):
        raise NotImplementedError
        
    def repair(self):
        raise NotImplementedError
        
    def backup(self):
        raise NotImplementedError

# Example Network Module Implementation
class NetworkModule(RepairModule):
    def __init__(self):
        super().__init__("Network", "Network diagnostics and repair")
        
    def scan(self):
        # Create a chain for network diagnostics
        network_scan_prompt = PromptTemplate(
            input_variables=["command_output"],
            template="Analyze network status:\n{command_output}\nIdentify issues:"
        )
        
        scan_chain = LLMChain(
            llm=llm,
            prompt=network_scan_prompt,
            memory=self.memory
        )
        
        # Run network diagnostics commands
        commands = [
            "ifconfig",
            "iwconfig",
            "systemctl status NetworkManager",
            "nmcli device status"
        ]
        
        results = []
        for cmd in commands:
            try:
                output = subprocess.check_output(cmd.split()).decode()
                results.append(scan_chain.run(command_output=output))
            except Exception as e:
                results.append(f"Error running {cmd}: {str(e)}")
                
        return results

# Main Application
class KaliRepairTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kali Linux Repair Tool")
        
        # Initialize modules
        self.modules = {
            "network": NetworkModule(),
            # Add other modules here
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        for module in self.modules.values():
            frame = ttk.LabelFrame(self.root, text=module.name)
            frame.pack(padx=5, pady=5, fill="x")
            
            ttk.Button(
                frame,
                text=f"Scan {module.name}",
                command=lambda m=module: self.run_scan(m)
            ).pack(side="left", padx=5)
            
    def run_scan(self, module):
        try:
            results = module.scan()
            messagebox.showinfo(
                f"{module.name} Scan Results",
                "\n".join(results)
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def run(self):
        self.root.mainloop()

# Run the application
if __name__ == "__main__":
    app = KaliRepairTool()
    app.run()