"""
法条检索匹配模块
处理OCR识别的文字，提取关键词，匹配相关法条
"""
from db_manager import LawDBManager
# OCR cancelled in project scope

class LawSearcher:
    def __init__(self):
        self.db_manager = LawDBManager()
        self.ocr_manager = None
    
    def process_image_and_search(self, image_path):
        """
        处理图片并检索相关法条（完整流程）
        Args:
            image_path: 图片路径
        Returns:
            {
                "recognized_text": "识别的文字",
                "keywords": ["关键词1", "关键词2"],
                "matched_laws": [...]
            }
        """
        # 1. OCR识别文字
        # OCR functionality was cancelled
        # Using direct text input instead
        recognized_text = image_path
        keywords = []
        
        # 2. 提取关键词
        
        # 3. 检索相关法条
        matched_laws = self.search_relevant_laws(recognized_text, keywords)
        
        return {
            "recognized_text": recognized_text,
            "keywords": keywords,
            "matched_laws": matched_laws
        }
    
    def search_relevant_laws(self, text, keywords):
        """
        根据文字和关键词检索相关法条
        Args:
            text: 识别的完整文字
            keywords: 提取的关键词列表
        Returns:
            匹配的法条列表
        """
        matched_laws = []
        seen_ids = set()
        
        # 策略1: 使用完整文字进行检索
        results = self.db_manager.search_laws(text, limit=5)
        for law in results:
            if law["id"] not in seen_ids:
                matched_laws.append(law)
                seen_ids.add(law["id"])
        
        # 策略2: 使用关键词逐个检索
        for keyword in keywords:
            if len(matched_laws) >= 10:  # 最多返回10条
                break
            
            results = self.db_manager.search_laws(keyword, limit=3)
            for law in results:
                if law["id"] not in seen_ids:
                    matched_laws.append(law)
                    seen_ids.add(law["id"])
        
        # 策略3: 使用法条类别检索（根据文字内容判断案件类型）
        category = self.determine_case_category(text)
        if category and len(matched_laws) < 10:
            results = self.db_manager.search_laws(category, limit=3)
            for law in results:
                if law["id"] not in seen_ids:
                    matched_laws.append(law)
                    seen_ids.add(law["id"])
        
        return matched_laws
    
    def determine_case_category(self, text):
        """
        根据文字内容判断案件类型/类别
        Returns:
            案件类别名称，如"治安管理处罚"、"刑事办案程序"等
        """
        category_keywords = {
            "治安管理处罚": ["拘留", "罚款", "警告", "违反治安管理"],
            "行政办案程序": ["行政案件", "调查", "证据", "处罚"],
            "刑事办案程序": ["刑事案件", "犯罪", "拘留", "逮捕", "立案"],
            "行政处罚程序": ["行政处罚", "罚款", "责令", "吊销"]
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return None
    
    def search_by_text(self, query_text):
        """
        直接文字搜索（手动输入搜索）
        Args:
            query_text: 搜索文字
        Returns:
            匹配的法条列表
        """
        return self.db_manager.search_laws(query_text, limit=20)
    
    def get_law_detail(self, law_id):
        """获取法条详情"""
        return self.db_manager.get_law_by_id(law_id)
    
    def add_new_law(self, law_name, article_number, article_content, category, keywords):
        """添加新法条（供管理员使用）"""
        return self.db_manager.add_law(law_name, article_number, article_content, category, keywords)
