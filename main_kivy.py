# -*- coding: utf-8 -*-
"""
执法辅助工具 - Kivy 版本（支持安卓打包）
使用 Kivy 框架，可打包成安卓APP
"""

import kivy
kivy.require('2.0.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, ListProperty

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 延迟导入搜索模块（避免启动时报错）
searcher = None

def get_searcher():
    global searcher
    if searcher is None:
        try:
            from law_searcher import LawSearcher
            searcher = LawSearcher()
        except Exception as e:
            print('[错误] 法条搜索模块加载失败:', e)
    return searcher


class LawResultItem(BoxLayout):
    """单条法条结果"""
    law_name = StringProperty('')
    article_number = StringProperty('')
    article_content = StringProperty('')
    
    def __init__(self, law_data, **kwargs):
        self.law_name = law_data.get('law_name', '')
        self.article_number = law_data.get('article_number', '')
        self.article_content = law_data.get('article_content', '')[:300]
        if len(law_data.get('article_content', '')) > 300:
            self.article_content += '...'
        super(LawResultItem, self).__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(10)
        self.spacing = dp(5)
        
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # 法条来源
        meta_label = Label(
            text='[color=1a73e8][b]《{}》{}[/b][/color]'.format(self.law_name, self.article_number),
            markup=True,
            size_hint_y=None,
            height=dp(25),
            halign='left',
            valign='middle',
            font_size=sp(14)
        )
        meta_label.bind(size=meta_label.setter('text_size'))
        self.add_widget(meta_label)
        
        # 法条内容
        content_label = Label(
            text=self.article_content,
            size_hint_y=None,
            height=dp(70),
            halign='left',
            valign='top',
            font_size=sp(13),
            text_size=(None, dp(70))
        )
        content_label.bind(size=content_label.setter('text_size'))
        self.add_widget(content_label)
    
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class MainScreen(BoxLayout):
    """主界面"""
    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(15)
        
        # 背景色
        with self.canvas.before:
            Color(0.96, 0.96, 0.98, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # 1. 标题
        title = Label(
            text='[size=24][b]⚖️ 执法辅助工具[/b][/size]',
            markup=True,
            size_hint_y=None,
            height=dp(60),
            font_size=sp(24)
        )
        self.add_widget(title)
        
        # 2. 搜索输入框
        self.search_input = TextInput(
            hint_text='输入关键词搜索法条（如：盗窃、拘留、罚款）',
            multiline=True,
            size_hint_y=None,
            height=dp(100),
            font_size=sp(16),
            padding=dp(10)
        )
        self.add_widget(self.search_input)
        
        # 3. 法律筛选下拉框
        self.law_filter = Spinner(
            text='全部法律',
            values=['全部法律', '治安管理处罚法', '公安机关办理行政案件程序规定', 
                   '公安机关办理刑事案件程序规定', '刑事诉讼法'],
            size_hint_y=None,
            height=dp(50),
            font_size=sp(16)
        )
        self.add_widget(self.law_filter)
        
        # 4. 搜索按钮
        search_btn = Button(
            text='🔍 搜索法条',
            size_hint_y=None,
            height=dp(50),
            font_size=sp(18),
            background_color=(0.05, 0.36, 0.75, 1)
        )
        search_btn.bind(on_press=self.do_search)
        self.add_widget(search_btn)
        
        # 5. 结果统计
        self.stats_label = Label(
            text='共 0 条结果',
            size_hint_y=None,
            height=dp(30),
            font_size=sp(14),
            halign='left'
        )
        self.stats_label.bind(size=self.stats_label.setter('text_size'))
        self.add_widget(self.stats_label)
        
        # 6. 结果滚动区域
        self.scroll = ScrollView()
        self.results_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(8)
        )
        self.results_container.bind(minimum_height=self.results_container.setter('height'))
        self.scroll.add_widget(self.results_container)
        self.add_widget(self.scroll)
        
        # 初始提示
        self.show_hint()
    
    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def show_hint(self):
        """显示初始提示"""
        self.results_container.clear_widgets()
        hint = Label(
            text='输入案情关键词，点击搜索\n\n示例：盗窃、打架斗殴、扰乱公共秩序',
            size_hint_y=None,
            height=dp(200),
            font_size=sp(14),
            color=(0.5, 0.5, 0.5, 1),
            halign='center'
        )
        hint.bind(size=hint.setter('text_size'))
        self.results_container.add_widget(hint)
        self.stats_label.text = '请输入关键词搜索'
    
    def do_search(self, instance):
        """执行搜索"""
        query = self.search_input.text.strip()
        
        if not query:
            self.show_hint()
            return
        
        # 获取搜索器
        s = get_searcher()
        if s is None:
            self.show_error('搜索模块加载失败')
            return
        
        # 执行搜索
        try:
            results = s.search_by_text(query)
            
            # 按法律筛选
            filter_law = self.law_filter.text
            if filter_law != '全部法律':
                # 简化筛选逻辑
                results = [r for r in results if filter_law in r.get('law_name', '')]
            
            self.show_results(results)
            
        except Exception as e:
            self.show_error('搜索失败: {}'.format(str(e)))
    
    def show_results(self, results):
        """显示搜索结果"""
        self.results_container.clear_widgets()
        
        if not results:
            self.stats_label.text = '未找到匹配的法条'
            empty = Label(
                text='未找到匹配的法条\n请尝试其他关键词',
                size_hint_y=None,
                height=dp(200),
                font_size=sp(14),
                color=(0.5, 0.5, 0.5, 1),
                halign='center'
            )
            empty.bind(size=empty.setter('text_size'))
            self.results_container.add_widget(empty)
            return
        
        self.stats_label.text = '共 {} 条结果'.format(len(results))
        
        for law in results[:20]:  # 最多显示20条
            item = LawResultItem(law)
            self.results_container.add_widget(item)
    
    def show_error(self, message):
        """显示错误"""
        self.results_container.clear_widgets()
        error = Label(
            text='❌ ' + message,
            size_hint_y=None,
            height=dp(200),
            font_size=sp(14),
            color=(0.8, 0.2, 0.2, 1),
            halign='center'
        )
        error.bind(size=error.setter('text_size'))
        self.results_container.add_widget(error)


class PoliceLawApp(App):
    """执法辅助工具应用"""
    
    def build(self):
        self.title = '执法辅助工具'
        return MainScreen()
    
    def on_stop(self):
        pass


if __name__ == '__main__':
    PoliceLawApp().run()
