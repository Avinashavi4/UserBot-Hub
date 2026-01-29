"""Safe Code Executor for data analysis and computations"""
import sys
import io
import traceback
from typing import Dict, Any, Optional
import ast
import math
import json
from contextlib import redirect_stdout, redirect_stderr


class CodeExecutor:
    """
    Safe Python code executor for data analysis
    Restricts dangerous operations while allowing useful computations
    """
    
    # Allowed modules for safe execution
    ALLOWED_MODULES = {
        'math': math,
        'json': json,
        'statistics': None,  # Will import on demand
        'datetime': None,
        'random': None,
        'collections': None,
        're': None,
    }
    
    # Blocked keywords for security
    BLOCKED_KEYWORDS = [
        'import os', 'import sys', 'import subprocess',
        '__import__', 'exec(', 'eval(', 'compile(',
        'open(', 'file(', 'input(',
        'globals(', 'locals(', 'vars(',
        '__builtins__', '__class__', '__bases__',
        'system(', 'popen(', 'spawn',
    ]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._setup_safe_builtins()
    
    def _setup_safe_builtins(self) -> Dict[str, Any]:
        """Create a restricted set of builtins"""
        safe_builtins = {
            # Safe built-in functions
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'int': int,
            'isinstance': isinstance,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'pow': pow,
            'print': print,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            # Math functions
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }
        return safe_builtins
    
    def _is_safe(self, code: str) -> tuple[bool, str]:
        """Check if code is safe to execute"""
        code_lower = code.lower()
        
        for blocked in self.BLOCKED_KEYWORDS:
            if blocked.lower() in code_lower:
                return False, f"Blocked keyword detected: {blocked}"
        
        # Try to parse the AST to check for dangerous nodes
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Block import statements
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module_name = node.names[0].name if isinstance(node, ast.Import) else node.module
                    if module_name not in self.ALLOWED_MODULES:
                        return False, f"Import of '{module_name}' not allowed"
                
                # Block attribute access to dangerous methods
                if isinstance(node, ast.Attribute):
                    if node.attr in ['__class__', '__bases__', '__subclasses__', '__mro__']:
                        return False, f"Access to '{node.attr}' not allowed"
                        
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        return True, "Code is safe"
    
    def execute(self, code: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code safely
        
        Args:
            code: Python code to execute
            variables: Optional dict of variables to make available
            
        Returns:
            Dict with 'success', 'output', 'error', and 'variables'
        """
        # Check safety
        is_safe, reason = self._is_safe(code)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"Security check failed: {reason}",
                "variables": {}
            }
        
        # Prepare execution environment
        safe_globals = {
            '__builtins__': self._setup_safe_builtins(),
            'math': math,
        }
        
        # Add user variables
        if variables:
            safe_globals.update(variables)
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result_vars = {}
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Execute the code
                exec(code, safe_globals)
            
            # Collect non-builtin variables
            for key, value in safe_globals.items():
                if not key.startswith('_') and key not in ['math']:
                    try:
                        # Only include serializable values
                        json.dumps(value)
                        result_vars[key] = value
                    except (TypeError, ValueError):
                        result_vars[key] = str(value)
            
            return {
                "success": True,
                "output": stdout_capture.getvalue(),
                "error": stderr_capture.getvalue(),
                "variables": result_vars
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": f"{type(e).__name__}: {str(e)}",
                "variables": {}
            }
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Safely evaluate a mathematical expression
        
        Args:
            expression: Math expression to evaluate
            
        Returns:
            Dict with 'success', 'result', 'error'
        """
        # Simple expression evaluation
        safe_names = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow, 'sqrt': math.sqrt,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'log10': math.log10, 'exp': math.exp,
            'pi': math.pi, 'e': math.e,
        }
        
        try:
            # Parse and validate expression
            tree = ast.parse(expression, mode='eval')
            
            # Only allow simple expressions
            for node in ast.walk(tree):
                if isinstance(node, (ast.Call,)):
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in safe_names:
                            raise ValueError(f"Function '{node.func.id}' not allowed")
            
            result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, safe_names)
            
            return {
                "success": True,
                "result": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }


# Test
if __name__ == "__main__":
    executor = CodeExecutor()
    
    # Test safe code
    result = executor.execute("""
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
average = total / len(numbers)
print(f"Sum: {total}, Average: {average}")
""")
    print("Safe code result:", result)
    
    # Test calculation
    calc = executor.calculate("sqrt(16) + pow(2, 3)")
    print("Calculation:", calc)
    
    # Test blocked code
    blocked = executor.execute("import os; os.system('ls')")
    print("Blocked code:", blocked)
