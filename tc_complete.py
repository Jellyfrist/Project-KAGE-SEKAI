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
    
        # Simple heuristic: if user message contains "product_id", call get_product_info directly
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
                        # Call the tool function with arguments
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
                        # Handle tool execution errors
                        messages.append({
                            "role": "function", 
                            "name": tool_name,
                            "content": f"Error: {e}"
                        })
                else:
                    return f"Tool {tool_name} not available"
        
        return "No result returned after max iterations"

if __name__ == "__main__":
    # Initialize the executor and register tools
    executor = ToolExecutor()
    executor.register_tools(ReviewTools())
    executor.register_tools(ProductTools())
    
    # Example user message
    user_message = """
        product_name: ลิปไก่ทอด,
        review_text: [
        "แท่นแบน หัวแปรงเรียว ดีมากก สีสวยมาก ปากฉ่ำมากก ไม่ลอกไม่ขุยไม่แห้ง ฉ่ำนาน ใช้แทนลิปมันไปแล้วว เริ่ดๆๆ ชอบมากๆ ได้มาโคตรคุ้ม มีกันแดดแถมด้วย สีลิปคือสวยมากกก น่ารักๆๆ ทาตัวเดียวจบ ปึ้ง เยี่ยมๆๆ",
        "เคมีหน่อยๆ มันฉุนๆหน่อย เฉยๆ ฉ่ำวาวแต่ไม่ชุ่มชื่น เวลาผ่านไปก็แห้งไปกับปาก แต่ติดทนอยู่ ฉ่ำวาว ได้ลองเทสสี สีสวยดี ลองทาที่ปากมันฉ่ำวาวแต่ไม่ชุ่มชื่น หนืดๆหน่อย ไม่ค่อยสบายปาก เวลาผ่านไปก็แห้งไปกับปากแต่สีติดทน ตอนออเดอร์ เรากด1แถม1ไป เราอยากยกเลิกแล้วเลือกสีใหม่แต่ทางแอดมินไม่กดยอมรับให้ ส่งของให้เลย เราก็นอยๆ เพราะอยากเปลี่ยนสีรู้สึกชอบสีชมพูม่วงๆ แต่อีกสีมันดูแดงออกส้มๆ เลยอยากเปลี่ยน เพราะตอนแรกดูในรูปคิดว่าน่าจะออกแดงๆพอรับได้ แต่ดูไปดูมากลัวไม่ชอบ กลัวออกส้มเลยอยากยกเลิกเปลี่ยนสีแต่ร้านไม่กดยอมรับ พอมาถึงก็ลอง เป็นอย่างที่คิดจริงๆ มันสีแอปเปิ้ลจริงมันแดงติดส้มซึ่งไม่ชอบ เราชอบสีที่ออกม่วงๆ อันนั้นสีสวยเลย เราลองทา วันต่อมา มีตุ่มที่ปาก ไปหาเภสัชซื้อยา เขาบอกเราแพ้ลิป มันก็มีแค่ตัวนี้ที่เราซื้อมาใหม่ ปกติใช้ลิปอันอื่นไม่เคยแพ้เลย แล้วเราก็ทำลิปตก ไม่ได้ตั้งใจทำตก แต่มันแตก ตกใจมาก งงด้วย ปกติลิปอันอื่นยี่ห้ออื่นๆไม่เคยแตกเลย เราไม่ได้คิดว่าจะแตกและะไม่ได้ตั้งใจทำตก แอบเสียดาย ทุกอย่างเลย นอยไม่ประทับใจโดยรวมๆ ลองทักแอดมินไป แอดมินบอกไม่ได้รับเคลม ที่ลูกค้าทำตก แต่เข้าใจ แต่มันนอยตั้งแต่สั่งซื้อ คุณภาพ แพ็คเกจ แล้วอะ ราคาก็ไม่ได้ถูก ลิปที่ราคาถูกกว่านี้ ยังทำให้พอใจได้กว่านี้ คงซื้อครั้งแรกและครั้งสุดท้าย",
        "เนื้อลิปดีมาก เม็ดสีแน่น ชอบความมีสีให้เลือกเยอะมากก และชอบการรีวิว สวอทสีให้ดูบนปากของนางแบบหลากหลายสีผิว และบนปากคล้ำ ส่วนเนื้อลิปดีมาก เม็ดสีแน่น กลิ่นหอม มีแค่ตัวแพคเกจที่ซึมออกมา ซึ่งจะรอของใหม่น้า ชอบ formula มากๆ อย่าเปลี่ยนนะคะ เปลี่ยนแค่แพคเกจจิ้งพอ เพราะเนื้อลิปดีมากกกกกก",
        "แพ้คเก้จก้องมากกก ลิปไหลเลอะกระเป๋าไปหมด ขนาดวางไว้ในห้องแอร์ต้องหาซองมาใส่ลิปยังไหลเลอะพกไปเติมไม่ได้ค่ะ ใส่กระเป๋าแล้วเลอะไปหมด เซ้งมากกก แต่ชอบสีชอบเนื้อนะ แต่เจอแบบนี้ไม่ไหวไหลตั้งแต่เปิดกล่องมาเลย ร้านจะให้ส่งคืนแต่คือมันก้เสียเวลาลูกค้าไง แต่คงไม่ซื้อละนอย เสียความรู้สึก สุดท้ายก้เลยทิ้งค่ะจบ",
        "ได้รับของมาลิปมีจุด ๆ แปลก ๆ เต็มเลย เหมือนในรูปแต่หนักกว่านี้มาก เราคิดว่าอาจจะต้องคนให้เข้ากัน เลยคนไปนิดนึง เพื่อนบอกว่าถ่ายรูปไว้ก่อน เราถ่ายไว้แล้วลองคนอีกรอบ พอลองทาดูลิปตกร่องในปากเป็นคราบเส้น ๆ เราเลยลองของเพื่อน เพื่อนสั่งมาเหมือนกันแต่เป็นอีกสี ก็ไม่ตกร่อง เนื้อไม่เหนียวเท่าของเราด้วย ทักไปถามแบรนด์ก่อนเพราะยังไม่อยากให้คะแนนน้อย ๆ ไปเลย ทางแบรนด์ตอบว่าเป็นปกติของลิปที่มีส่วนผสมเป็น oil ให้ใช้แปรงคน ๆ แล้วใช้ได้ปกติ เราเลยตอบไปว่าเราคนแล้ว มันได้แค่นี้ จริง ๆ มันหนักกว่านี้ด้วย แบรนด์ก็ตอบกลับมาเหมือนเดิม อย่างกับก็อปวาง ตอนแรกหวังว่าแบรนด์จะเปลี่ยนให้ เพราะเราไม่สบายใจจริง ๆ เราสั่งลิปมาพร้อมกับบลัช บลัชมีจุด ๆ ที่หน้าบลัชเหมือนกัน แต่พอปาดมาใช้มันปกติ เราก็โอเคใช้ได้ แต่ลิปมันไม่เหมือนกัน เลยอยากเปลี่ยน แต่ตอนนี้ไม่ได้หวังอะไรจากแบรนด์แล้วค่ะ ก็พอแค่นี้แหละ เสียความรู้สึกไปแล้ว เราเปิดใจกลับมาใช้แบรนด์ไทยอีกครั้งเพราะแบรนด์นี้ แล้วก็ผิดหวัง เสียใจจริง ๆ",
        "ลองซื้อลิปกลอสตัวนี้มาใช้ คือดีเกินคาด ปากดูฉ่ำสวยแต่ไม่เหนียวเหนอะเลย สีคือโคตรน่ารัก ทาเดี่ยว ๆ ก็รอด ทาทับลิปก็ยิ่งปัง พกติดกระเป๋าตลอดเลยตอนนี้ ใช้จริงปลื้มจริง สีเบอร์12ออกแดงอมม่วงสวยสุดๆ",
        "🎨ความหลากหลายของสี：มีสีเยอะหลากหลายดี สีน้ำตาลเข้มหน่อย แต่ยังมีความโปร่งของสี 💧ผลการให้ความชุ่มชื้น：วาวมาก ชุ่มชื้น ไม่เหนียวเกินไป ⏳ติดทนนาน：เหมือนกลอสมีสีหน่อยๆ ไม่ทนมาก แต่ชอบนะ เหมาะสำหรับการสวมใส่ทุกวัน, สีสันสดใสและทันสมัย",
        "สี 10 สวยนะ สีปากฟีลลูกคุณ ชมพูน่ารักดี แต่คนปากคล้ำต้องทาทับหลายรอบหน่อยค่ะ ส่วนตัวที่ใช้ลิปกลอสมา แบรนด์นี้คือเหนียวสุด😅",
        "มีสีสันสดใส, สีสวย07สีมันเหมือนจะแดงแต่มีความออกส้มๆนิดเดียวอันนี้นิดเดียวจริงสีส้มสำหรับเรานะ มันเป็นลิปฟิวลิปกลอสระหว่างวันมันก็ไม่ติดปากอยู่แล้วอันนี้ต้องเติมระหว่างวัน ของเรามันแบบซึมมันอาจจะเป็นส่วนน้อยของคนอื่นไม่รู้เป็นไงแต่รอทางแบรนด์ปรับปรุง",
        "มันเหนียว ทาแล้วไม่สวยเท่าที่คิดค่ะ เท็กเจอร์แปลกนิดหน่อย จะกลอสก็ไม่วาวขนาดนั้น แล้วก็ไม่ได้ติดทนด้วย",
        "ลิปไก่ทอดของจริงค่ะ สมชื่อมากกก สีสวยไม่เหนียวเลย ตอนแรกลังเลจะซื้อนานมากเพราะคิดว่าลิปแบบนี้มันไม่ติดทน ทาแป๊บ ๆ ก็คงหลุดหมด สรุปคือติดทนระดับนึงเลย แล้วสีธรรมชาติสุด ๆ ที่สำคัญกลิ่นคือห้อมมมแบบตะโกน!!! แพ็คมาดี ไม่มีเสียหายคับบบ",
        "ของไม่มีอะไรเสียหาย ลิปมีกลิ่นหอมอ่อนๆพอลองทาดูส่วนตัว รู้สึกว่าไม่แดงมากตุ่นๆ ทั้งนี้น่าจะอยู่กับผิวของคนที่ทาด้วย ไม่ได้ติดทนมากแต่ทาเพิ่มได้ไม่ซีเรียส รวมๆแล้วคือโช๊ะ ฟิรมากคุนน้า",
        "ไม่รู้ชงหรืออะไร เหมือนได้สินค้าหลุดQCมาลิปมีรอยหมึก สีน้ำเงินมาแอมากลองเช็ดก็ไม่ออกT^T ส่วนเนื้อลิปทาทิ้งไว้ประมาณ5นาทีแล้วเช็ดออกไม่ทิ้งสเตนอะไรเลยแอบผิดหวังมาก",
        "ตอนแรกก็ดีนะคะสีสวย แต่ มันซึมออกมาเยอะมากเลยค่ะเหมือนไม่แน่น แล้วซึมออกมาไม่ใช่ที่ตรงเปิดนะคะ ซึมนิดเดียวพอได้ค่ะ แต่เปิดใช้ที่ทะลักออกมาตรงขอบๆ 9กรัมน่าจะไม่พอนะคะแบบนี้",
        "เนื้อกลอสดี ทาแล้วปากชุมชื้น แต่อยากให้ทำแบบที่เป็นสีเทาไปเลยไม่ต้องคิดม่วง เพราะเวลาติดม่วงเวลาเอามาเบลนกับสีพวกโทนแดง มันจะติดม่วงไปด้วยซึ่งจริงๆจุดประสงค์ของลิปเบลน คือทำให้สีมันละทุนขึ้นกว่าเดิม เลยอยากให้เป็นลิปเบลนที่ติดเทาๆไปเลยเพื่อที่เวลาเอามาเบลนแล้วจะได้สีที่ดูตุ่นขึ้นเท่านั้น"
        ]
        กรุณาวิเคราะห์รีวิวนี้ตาม schema ที่กำหนด
        """
    
    # Execute with tools
    result = executor.execute_with_tools(user_message)
    print("Final Result:\n", result)
