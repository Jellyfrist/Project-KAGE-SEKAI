from litellm import completion
import json
from typing import List, Dict, Any
from config import MODEL

# import the tool classes
from tc_analyze_review import ReviewTools
from tc_get_product_info import ProductTools

class ToolExecutor:
    def __init__(self):
        """Main executor class that manages tools and handles LLM function calling"""
        self.tools = {}
        self.tool_schemas = []
    
    def register_tool(self, name: str, func: callable, schema: dict):
        """Register a single tool with its execution function and schema"""
        self.tools[name] = func
        self.tool_schemas.append(schema)
    
    def register_tools(self, tool_class_instance):
        """Register all tools from a tool class instance"""
        schemas = tool_class_instance.get_schemas()
        for i, schema in enumerate(schemas):
            tool_name = schema["name"]
            tool_func = getattr(tool_class_instance, tool_name)
            self.register_tool(tool_name, tool_func, schema)
    
    def execute_with_tools(self, user_message: str, model: str = MODEL, max_iterations: int = 3) -> str:
        messages = [{"role": "user", "content": user_message}]
    
        if "product_id" in user_message:
            # get product_id
            try:
                start = user_message.index("product_id:") + len("product_id:")
                end = user_message.index(",", start)
                product_id = user_message[start:end].strip()
            except:
                return "ไม่พบ product_id ที่ระบุ"
        
            # called get_product_info
            tool = self.tools.get("get_product_info")
            if not tool:
                return "Tool get_product_info not available"
        
            result = tool(product_id=product_id)
            return json.dumps(result, ensure_ascii=False, indent=2)

        else:
            # doesn't have product_id -> use analyze_review
            iteration = 0
            while iteration < max_iterations:
                iteration += 1

                response = completion(
                    model=model,
                    messages=messages,
                    functions=self.tool_schemas,
                    function_call="auto"
                )
        
                # Extract message safely in Object or Dict format
                message = getattr(response.choices[0], "message", response.choices[0].get("message"))
            
                # Step 2: Check if LLM wants to call a function
                if not getattr(message, "function_call", None):
                    content = getattr(message, "content", None) or message.get("content")
                    try:
                        parsed = json.loads(content)
                        return json.dumps(parsed, ensure_ascii=False, indent=2)
                    except:
                        return content
            
                # Step 3: Execute the requested tool
                tool_name = message.function_call.name
                tool_args = json.loads(message.function_call.arguments)
            
                if tool_name in self.tools:
                    try:
                        tool_result = self.tools[tool_name](**tool_args)
                    
                        # Step 4: Add tool call and result to conversation history (สวยขึ้นด้วย json.dumps)
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "function_call": {
                                "name": tool_name,
                                "arguments": message.function_call.arguments
                            }
                        })
                
                        messages.append({
                            "role": "function",
                            "name": tool_name,
                            "content": json.dumps(tool_result, ensure_ascii=False, indent=2)
                        })
        
                    except Exception as e:
                        # Handle tool execution error
                        messages.append({
                            "role": "function", 
                            "name": tool_name,
                            "content": f"Error: {e}"
                        })
                else:
                    return f"Tool {tool_name} not available"


if __name__ == "__main__":
    # Initialize the executor and register tools
    executor = ToolExecutor()
    executor.register_tools(ReviewTools())
    executor.register_tools(ProductTools())
    
    # Example user message
    user_message = """
        product_id: M001,
        product name: มาสคาร่าคิ้ว KAGE,
        review text: รูสึกวาแปลงใชงานยาก เป็นคราบ เลอะง่าย พยามบองใช้
 ผลายนอมาก แตไม่ได้จริงๆ 🥹🥹🥹 เนื้อมาสคาลาคิ้วออกมาเยอะมาก แล้วเลณอะเทอะสุดๆ ถ้าเป็นแปลงแบบอื่น
 น่าจะดีกวานี้ หัวแปลงนี้ใช้ยาก
    """
    
    # Execute with tools
    result = executor.execute_with_tools(user_message)
    print("Final Result:\n", result)
