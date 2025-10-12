import json
from litellm import completion
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
	
	def execute_with_tools(self, user_message: str, model: str = MODEL, max_iterations: int = 6) -> str:
		# 1. start conversation with user message
		messages = [{"role": "user", "content": user_message}]

		iteration = 0
		last_tool_result_json = None 

		while iteration < max_iterations:
			iteration += 1

			# 2. call LLM with available tools
			response = completion(
				model=model,
				messages=messages,
				functions=self.tool_schemas,
				function_call="auto"
			)

			# extract message safely (works whether it's object or dict)
			message = getattr(response.choices[0], "message", response.choices[0].get("message"))

			# 3. check if LLM wants to call a function
			function_call = getattr(message, "function_call", None) or message.get("function_call")

			if function_call:
				tool_name = function_call.name if hasattr(function_call, "name") else function_call.get("name")
				print("LLM requested tool:", tool_name)

				# try to parse arguments (some SDKs return dict already)
				raw_args = function_call.arguments if hasattr(function_call, "arguments") else function_call.get("arguments")
				try:
					tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args or {}
				except json.JSONDecodeError:
					# let LLM know arguments were invalid and continue
					messages.append({
						"role": "function",
						"name": tool_name,
						"content": "Error: Invalid JSON arguments provided by LLM."
					})
					continue

				if tool_name in self.tools:
					try:
						# execute the tool function
						tool_result = self.tools[tool_name](**tool_args)

						# ensure tool_result is JSON-serializable and not None
						if tool_result is None:
							tool_result = {"result": None}

						try:
							# use ensure_ascii=False to preserve Unicode characters
							tool_result_json = json.dumps(tool_result, ensure_ascii=False, indent=2)
						except TypeError:
							tool_result_json = json.dumps(str(tool_result), ensure_ascii=False, indent=2)
							
						# save the last tool result in case LLM returns empty
						last_tool_result_json = tool_result_json 
						
						# 4. add the assistant's original message (the function call) to history
						messages.append(message if isinstance(message, dict) else {
							"role": "assistant",
							"content": "",
							"function_call": {
								"name": tool_name,
								"arguments": raw_args
							}
						})

						# add the function result as a function response
						messages.append({
							"role": "function",
							"name": tool_name,
							"content": tool_result_json
						})

						# continue loop so LLM can respond using the tool result
					
					except Exception as e:
						messages.append({
							"role": "function",
							"name": tool_name,
							"content": f"Error during tool execution: {e}"
						})
						print("Tool execution exception:", e) 
				else:
					return f"Tool {tool_name} not available"

			else:
				# 5. no function call, return the final content from LLM (Summary)
				content = getattr(message, "content", None) or message.get("content")

				if content:
					# try to parse as JSON first
					try:
						parsed = json.loads(content)
						return json.dumps(parsed, ensure_ascii=False, indent=2)
					except (json.JSONDecodeError, TypeError):
						# return in natural language
						return content
				else:
					# if LLM returned empty content, return last tool result
					if last_tool_result_json:
						raw_json_data = json.loads(last_tool_result_json)
						
						if 'aspects' in raw_json_data:
							del raw_json_data['aspects']

						clean_json_result = json.dumps(raw_json_data, ensure_ascii=False, indent=2)
						return clean_json_result

					return "LLM returned an empty response and no tool was executed."

		# if max iterations reached, return last tool result
		if last_tool_result_json:
			raw_json_data = json.loads(last_tool_result_json)
			if 'aspects' in raw_json_data:
				del raw_json_data['aspects']
				
			clean_json_result = json.dumps(raw_json_data, ensure_ascii=False, indent=2)
			return clean_json_result

		return "No result returned after max iterations"

if __name__ == "__main__":

    # 1. create tool instances
    try:
        review_tool_instance = ReviewTools()
        product_tool_instance = ProductTools()
        
    except Exception as e:
        print(f"❌ Error: ไม่สามารถสร้าง Tool Instance ได้: {e}")
        print("โปรดตรวจสอบว่าไฟล์ tc_analyze_review.py และ tc_get_product_info.py มีข้อผิดพลาดหรือไม่")
        exit()

    executor = ToolExecutor()

    # 2. add tools to executor
    try:
        executor.register_tools(review_tool_instance)
        executor.register_tools(product_tool_instance)
        print("✅ Tools ถูกลงทะเบียนเรียบร้อยแล้ว: [analyze_review, get_product_info]")
    except Exception as e:
        print(f"❌ Error: การลงทะเบียน Tools ล้มเหลว: {e}")
        exit()

    # 3. add user message for testing
    user_message = """
วิเคราะห์รีวิวสำหรับสินค้า 'ลิปไก่ทอด' จากไฟล์ csv_path: reviews/syrup_glossy_lip_reviews.csv

เมื่อวิเคราะห์เสร็จสิ้นด้วย Tool แล้ว:
1. โปรดสรุปผลการวิเคราะห์ทั้งหมดเป็นภาษาไทย โดยเน้นที่จุดแข็งและจุดอ่อนหลักๆ ในแง่มุมต่างๆ (คุณภาพ, ราคา, บริการ, การจัดส่ง, บรรจุภัณฑ์)
2. ให้คำแนะนำเชิงกลยุทธ์แก่เจ้าของธุรกิจ 3 ส่วน:
    a. **คำแนะนำด้านการปรับปรุงผลิตภัณฑ์/บรรจุภัณฑ์:** ระบุแนวทางแก้ไขปัญหาจุดอ่อนหลัก โดยอาจอ้างอิงถึงแนวทางปฏิบัติที่ดีที่สุด (Best Practices) ในธุรกิจเครื่องสำอาง ทั้งในประเทศและต่างประเทศ
    b. **คำแนะนำด้านการบริการลูกค้า:** ระบุมาตรการแก้ไขปัญหาด้านบริการลูกค้าที่พบ
    c. **คำแนะนำด้านการตลาด:** ระบุว่าควรนำจุดแข็ง/รีวิวใดไปใช้ในการทำการตลาดเพื่อดึงดูดลูกค้าใหม่ได้บ้าง (เน้นข้อความที่น่าสนใจจากรีวิวที่เป็นจุดแข็ง)
**ตอบกลับด้วยข้อความสรุปและคำแนะนำเท่านั้น (ใช้ Markdown/ตารางที่สวยงาม) ไม่ต้องแสดงผลลัพธ์ JSON ดิบ**
"""

    analysis_target = 'วิเคราะห์รีวิวสำหรับสินค้า \'ลิปไก่ทอด\' จากไฟล์ csv_path: reviews/syrup_glossy_lip_reviews.csv'
    print("\n--- เริ่มการวิเคราะห์รีวิว ---")
    print(f"User Request: {analysis_target}")

    try:
        # call the executor with user message
        result = executor.execute_with_tools(user_message)

        print("\n--- สรุปผลการวิเคราะห์และคำแนะนำเชิงกลยุทธ์ ---\n")
        print(result)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดในการรันโปรแกรม: {e}")

    
    # 4. addd teat case for get_product_info
    print("\n--- เริ่มการทดสอบ get_product_info ---")
    product_id_test = "C002"
    user_message_product = f"ฉันต้องการข้อมูลเชิงกลยุทธ์ของสินค้า ID {product_id_test} เพื่อวางแผนการตลาด"
    print(f"User Request: {user_message_product}")
    
    try:
        result_product = executor.execute_with_tools(user_message_product)
        print(f"\n--- ผลลัพธ์สำหรับ Product ID {product_id_test} ---\n")
        print(result_product)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดในการรัน Tool get_product_info: {e}")
