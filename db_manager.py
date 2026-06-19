"""
法律法规数据库管理模块
负责SQLite数据库的创建、初始化和查询
"""
import sqlite3
import os

class LawDBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # 使用脚本所在目录的 laws.db，避免工作目录不同导致连错数据库
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(os.path.dirname(base_dir), 'laws.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库，创建表格并导入法条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建法条表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS laws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            law_name TEXT NOT NULL,
            article_number TEXT,
            article_content TEXT NOT NULL,
            category TEXT,
            keywords TEXT
        )
        ''')
        
        # 创建全文检索虚拟表
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
            law_name,
            article_number,
            article_content,
            category,
            keywords,
            content=laws,
            content_rowid=id
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # 导入初始法条数据
        self.import_initial_data()
    
    def import_initial_data(self):
        """导入初始法律法规数据"""
        initial_laws = [
            {
                "law_name": "中华人民共和国治安管理处罚法",
                "article_number": "第二十五条",
                "article_content": "有下列行为之一的，处五日以下拘留或者五百元以下罚款；情节较重的，处五日以上十日以下拘留，可以并处五百元以下罚款：（一）散布谣言，谎报险情、疫情、警情或者以其他方法故意扰乱公共秩序的；（二）投放虚假的爆炸性、毒害性、放射性、腐蚀性物质或者传染病病原体等危险物质扰乱公共秩序的；（三）扬言实施放火、爆炸、投放危险物质扰乱公共秩序的。",
                "category": "治安管理处罚",
                "keywords": "谣言,险情,疫情,警情,公共秩序,爆炸,毒害,放射性"
            },
            {
                "law_name": "中华人民共和国治安管理处罚法",
                "article_number": "第四十九条",
                "article_content": "盗窃、诈骗、哄抢、抢夺、敲诈勒索或者故意损毁公私财物的，处五日以上十日以下拘留，可以并处五百元以下罚款；情节较重的，处十日以上十五日以下拘留，可以并处一千元以下罚款。",
                "category": "财产违法犯罪",
                "keywords": "盗窃,诈骗,哄抢,抢夺,敲诈勒索,故意损毁,公私财物"
            },
            {
                "law_name": "公安机关办理行政案件程序规定",
                "article_number": "第三十七条",
                "article_content": "对行政案件进行调查时，应当合法、及时、客观、全面地收集、调取证据材料，并予以审查、核实。",
                "category": "行政办案程序",
                "keywords": "行政案件,调查,证据,收集,调取"
            },
            {
                "law_name": "公安机关办理刑事案件程序规定",
                "article_number": "第一百七十一条",
                "article_content": "对接受的案件，或者发现的犯罪线索，公安机关应当迅速进行审查。发现案件事实或者线索不明的，必要时，经公安机关负责人批准，可以进行初查。",
                "category": "刑事办案程序",
                "keywords": "刑事案件,审查,犯罪线索,初查"
            },
            {
                "law_name": "中华人民共和国行政处罚法",
                "article_number": "第四十四条",
                "article_content": "行政机关在作出行政处罚决定之前，应当告知当事人拟作出的行政处罚内容及事实、理由、依据，并告知当事人依法享有的陈述、申辩、要求听证等权利。",
                "category": "行政处罚程序",
                "keywords": "行政处罚,告知,陈述,申辩,听证"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM laws")
        count = cursor.fetchone()[0]
        
        if count == 0:
            for law in initial_laws:
                cursor.execute('''
                INSERT INTO laws (law_name, article_number, article_content, category, keywords)
                VALUES (?, ?, ?, ?, ?)
                ''', (law["law_name"], law["article_number"], 
                      law["article_content"], law["category"], law["keywords"]))
            
            # 同步到FTS表
            cursor.execute('''
            INSERT INTO laws_fts(rowid, law_name, article_number, article_content, category, keywords)
            SELECT id, law_name, article_number, article_content, category, keywords
            FROM laws
            ''')
        
        conn.commit()
        conn.close()
    
    def search_laws(self, query, limit=10):
        """
        检索法条（中文优化：LIKE 查询 + 多关键词展开 + 相关性排序）
        1. 先找所有匹配的法条
        2. 按匹配关键词数量排序（匹配越多越相关）
        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
        Returns:
            匹配的法条列表（按相关性排序）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 提取所有子关键词（2字及以上）
        sub_keywords = []
        if len(query) >= 2:
            seen_subs = set()
            for length in [3, 2]:  # 优先3字词，再2字词
                for i in range(len(query) - length + 1):
                    sub = query[i:i+length]
                    if sub and sub not in seen_subs:
                        seen_subs.add(sub)
                        sub_keywords.append(sub)
        else:
            sub_keywords = [query]
        
        # 搜索所有匹配的法条，统计每个法条匹配了多少个关键词
        matched = {}  # id -> {law info + match_count}
        
        for sub in sub_keywords:
            pattern = '%' + sub + '%'
            cursor.execute('''
            SELECT id, law_name, article_number, article_content, category, keywords
            FROM laws
            WHERE article_content LIKE ? OR keywords LIKE ? OR article_number LIKE ?
            ''', (pattern, pattern, pattern))
            
            for row in cursor.fetchall():
                law_id = row[0]
                if law_id not in matched:
                    matched[law_id] = {
                        "id": row[0],
                        "law_name": row[1],
                        "article_number": row[2],
                        "article_content": row[3],
                        "category": row[4],
                        "keywords": row[5],
                        "match_count": 0,
                        "match_keywords": []
                    }
                matched[law_id]["match_count"] += 1
                matched[law_id]["match_keywords"].append(sub)
        
        conn.close()
        
        # 按匹配数量降序排序，再按法律名称和条号升序
        sorted_results = sorted(
            matched.values(),
            key=lambda x: (-x["match_count"], x["law_name"], x["article_number"])
        )
        
        # 移除辅助字段后返回
        for r in sorted_results[:limit]:
            r.pop('match_count', None)
            r.pop('match_keywords', None)
        
        return sorted_results[:limit]
    
    def get_law_by_id(self, law_id):
        """根据ID获取法条详情"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, law_name, article_number, article_content, category, keywords
        FROM laws
        WHERE id = ?
        ''', (law_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "law_name": row[1],
                "article_number": row[2],
                "article_content": row[3],
                "category": row[4],
                "keywords": row[5]
            }
        return None
    
    def add_law(self, law_name, article_number, article_content, category, keywords):
        """添加新法条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO laws (law_name, article_number, article_content, category, keywords)
        VALUES (?, ?, ?, ?, ?)
        ''', (law_name, article_number, article_content, category, keywords))
        
        # 获取新插入的ID
        law_id = cursor.lastrowid
        
        # 同步到FTS表
        cursor.execute('''
        INSERT INTO laws_fts(rowid, law_name, article_number, article_content, category, keywords)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (law_id, law_name, article_number, article_content, category, keywords))
        
        conn.commit()
        conn.close()
        
        return law_id
