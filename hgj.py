import json
import os
import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

#
# 전역 설정: 폰트 등록
#
current_dir = os.path.dirname(__file__)
font_path = os.path.join(current_dir, "batang.ttc")  # .ttc가 문제 있을 경우 .ttf 사용 권장
LabelBase.register(name="batang", fn_regular=font_path)

#
# 간단히 지역 간 인접 관계 정의 (이전과 동일)
#
REGION_ADJACENCY = {
    "평안북도": ["함경북도", "평안남도"],
    "함경북도": ["평안북도", "함경남도"],
    "평안남도": ["평안북도", "함경남도", "황해도"],
    "함경남도": ["함경북도", "평안남도"],
    "황해도": ["평안남도", "강원도"],
    "강원도": ["황해도", "경기도"],
    "경기도": ["강원도", "충청북도"],
    "충청북도": ["경기도", "충청남도"],
    "충청남도": ["충청북도", "경상북도"],
    "경상북도": ["충청남도", "경상남도"],
    "경상남도": ["경상북도", "전라북도"],
    "전라북도": ["경상남도", "전라남도"],
    "전라남도": ["전라북도", "제주도"],
    "제주도": ["전라남도"]
}

AI_NAMES = [
    "김유진", "김유정", "김선유", "김민유", "이동호",
    "이병호", "김윤희", "신문주", "신선우", "김혜정",
    "김권성", "김경남", "김민주"
]

# ----------------------
# 지역(Region) 클래스
# ----------------------
class Region:
    def __init__(self, name, owner=None):
        self.name = name
        self.owner = owner  # 소유자 (플레이어명 또는 AI명)

        # 자원
        self.gold = 1000
        self.food = 3000
        self.population = 1000

        # 능력치
        self.agri = 0      # 농업
        self.commerce = 0  # 상업
        self.security = 0  # 치안

        # 병력(명 수)
        self.army = 0
    
    def invest_agri(self):
        if self.gold >= 100:
            self.gold -= 100
            self.agri += 1
    
    def invest_commerce(self):
        if self.gold >= 100:
            self.gold -= 100
            self.commerce += 1
    
    def invest_security(self):
        if self.gold >= 100:
            self.gold -= 100
            self.security += 1
    
    def recruit_army(self, amount):
        # 병사 1명당 식량 5 소모, 인구 1 감소
        cost_food = amount * 5
        if self.food >= cost_food and self.population >= amount:
            self.food -= cost_food
            self.population -= amount
            self.army += amount
    
    def next_turn(self):
        # 턴이 끝날 때마다 자원 증가
        self.gold += 100
        self.food += 300
        self.population += 100
        
        # 능력치 효과 (질문 예시대로 0.003 / 0.002 적용)
        if self.agri > 0:
            self.food += int(self.food * 0.003 * self.agri)
        if self.commerce > 0:
            self.gold += int(self.gold * 0.002 * self.commerce)
        if self.security > 0:
            self.population += int(self.population * 0.01 * self.security)
        
        # 병사 유지비
        if self.army > 0:
            food_cost = self.army // 10
            if self.food >= food_cost:
                self.food -= food_cost
            else:
                self.food = 0

# ----------------------
# 전투 로직 함수 (한 번의 교환으로 승패 결정)
# ----------------------
def do_battle_attack(attacker_soldiers, defender_soldiers):
    if attacker_soldiers <= 0:
        return 0, defender_soldiers
    if defender_soldiers <= 0:
        return attacker_soldiers, 0

    atk_attack = attacker_soldiers * 20
    atk_hp = attacker_soldiers * 30

    def_attack = defender_soldiers * 20
    def_hp = defender_soldiers * 30

    # 공격군이 먼저 수비군 HP를 깎음
    old_def_hp = def_hp
    def_hp -= atk_attack
    if def_hp < 0:
        def_hp = 0
    
    lost_ratio_def = atk_attack / old_def_hp if old_def_hp > 0 else 1.0
    lost_soldiers_def = int(defender_soldiers * lost_ratio_def)
    defender_after = defender_soldiers - lost_soldiers_def
    if defender_after < 0:
        defender_after = 0

    # 수비군이 생존했다면 반격
    if defender_after > 0:
        old_atk_hp = atk_hp
        atk_hp -= def_attack
        if atk_hp < 0:
            atk_hp = 0
        
        lost_ratio_atk = def_attack / old_atk_hp if old_atk_hp > 0 else 1.0
        lost_soldiers_atk = int(attacker_soldiers * lost_ratio_atk)
        attacker_after = attacker_soldiers - lost_soldiers_atk
        if attacker_after < 0:
            attacker_after = 0
    else:
        attacker_after = attacker_soldiers

    return attacker_after, defender_after

# ----------------------
# 메인 메뉴 스크린
# ----------------------
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        start_btn = Button(text="Start", font_name="batang", size_hint=(1, 0.2))
        load_btn = Button(text="Load", font_name="batang", size_hint=(1, 0.2))
        settings_btn = Button(text="Settings", font_name="batang", size_hint=(1, 0.2))
        exit_btn = Button(text="Exit", font_name="batang", size_hint=(1, 0.2))
        
        start_btn.bind(on_release=self.start_game)
        load_btn.bind(on_release=self.load_game)
        settings_btn.bind(on_release=self.open_settings)
        exit_btn.bind(on_release=self.exit_game)
        
        layout.add_widget(start_btn)
        layout.add_widget(load_btn)
        layout.add_widget(settings_btn)
        layout.add_widget(exit_btn)
        
        self.add_widget(layout)
    
    def start_game(self, instance):
        self.manager.current = "startregion"
    
    def load_game(self, instance):
        self.manager.current = "load"
    
    def open_settings(self, instance):
        self.manager.current = "settings"
    
    def exit_game(self, instance):
        App.get_running_app().stop()

# ----------------------
# 지역 선택 + 플레이어 이름 입력 스크린
# ----------------------
class StartRegionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # 플레이어 이름 입력
        self.name_input = TextInput(
            text="주인공",
            multiline=False,
            font_name="batang",
            size_hint=(1, 0.1)
        )
        self.layout.add_widget(self.name_input)

        label = Label(text="시작 지역을 선택하세요", font_name="batang")
        self.layout.add_widget(label)
        
        self.regions_list = [
            "평안북도", "평안남도", "함경북도", "함경남도", "황해도",
            "강원도", "경기도", "경상남도", "경상북도", "전라남도",
            "전라북도", "충청북도", "충청남도", "제주도"
        ]
        
        for r in self.regions_list:
            btn = Button(text=r, size_hint=(1, 0.1), font_name="batang")
            btn.bind(on_release=self.select_region)
            self.layout.add_widget(btn)
        
        self.add_widget(self.layout)
    
    def select_region(self, instance):
        player_name = self.name_input.text.strip()
        if not player_name:
            player_name = "플레이어"  # 디폴트값
        
        selected_region = instance.text
        
        # GameScreen에 플레이어 이름 / 선택 지역 전달
        game_screen = self.manager.get_screen("game")
        game_screen.player_name = player_name
        game_screen.player_region_name = selected_region
        
        self.manager.current = "game"

# ----------------------
# 게임 플레이 스크린 (맵 화면)
# ----------------------
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.player_name = None         # 플레이어 입력 이름
        self.player_region_name = None  # 플레이어가 첫 선택한 지역
        self.regions = {}              # 모든 지역 정보 (name -> Region)

        # "현재 선택된 내 땅" 관리
        self.selected_region_name = None  
        self.selected_region_index = 0   # 내 땅 리스트를 순환하기 위한 인덱스
        
        self.layout = BoxLayout(orientation='vertical', spacing=5, padding=5)
        self.info_label = Label(text="게임 화면입니다.", font_name="batang")
        self.layout.add_widget(self.info_label)
        
        # 버튼들 레이아웃
        button_layout = BoxLayout(size_hint=(1, 0.2))
        
        # (1) 땅 선택 버튼
        self.select_region_btn = Button(text="땅 선택", font_name="batang", size_hint=(1, 1))
        self.select_region_btn.bind(on_release=self.select_owned_region_action)
        
        # (2) 투자 버튼들 (3개)
        self.invest_agri_btn = Button(text="농업투자", font_name="batang", size_hint=(1, 1))
        self.invest_commerce_btn = Button(text="상업투자", font_name="batang", size_hint=(1, 1))
        self.invest_security_btn = Button(text="치안투자", font_name="batang", size_hint=(1, 1))
        
        # (3) 모병 버튼
        self.recruit_btn = Button(text="모병", font_name="batang", size_hint=(1, 1))
        
        # (4) 공격 버튼
        self.attack_btn = Button(text="공격", font_name="batang", size_hint=(1, 1))
        
        # (5) 저장 / 턴 종료
        self.save_btn = Button(text="저장", font_name="batang", size_hint=(1, 1))
        self.next_turn_btn = Button(text="턴 종료", font_name="batang", size_hint=(1, 1))
        self.exit_btn = Button(text="종료", font_name="batang", size_hint=(1, 1))
        
        # 버튼 이벤트 바인딩
        self.invest_agri_btn.bind(on_release=self.invest_agri_action)
        self.invest_commerce_btn.bind(on_release=self.invest_commerce_action)
        self.invest_security_btn.bind(on_release=self.invest_security_action)
        self.recruit_btn.bind(on_release=self.recruit_action)
        self.attack_btn.bind(on_release=self.attack_action)
        self.save_btn.bind(on_release=self.save_game)
        self.next_turn_btn.bind(on_release=self.next_turn)
        self.exit_btn.bind(on_release=self.exit_game)

        # 버튼들을 레이아웃에 배치
        button_layout.add_widget(self.select_region_btn)
        button_layout.add_widget(self.invest_agri_btn)
        button_layout.add_widget(self.invest_commerce_btn)
        button_layout.add_widget(self.invest_security_btn)
        button_layout.add_widget(self.recruit_btn)
        button_layout.add_widget(self.attack_btn)
        button_layout.add_widget(self.save_btn)
        button_layout.add_widget(self.next_turn_btn)
        button_layout.add_widget(self.exit_btn)
        self.layout.add_widget(button_layout)
        
        # 스크롤뷰 + GridLayout (지역 정보 표시)
        self.scroll_view = ScrollView(size_hint=(1, 0.6))
        self.regions_layout = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.regions_layout.bind(minimum_height=self.regions_layout.setter('height'))
        self.scroll_view.add_widget(self.regions_layout)
        
        self.layout.add_widget(self.scroll_view)
        self.add_widget(self.layout)
    
    def exit_game(self, instance):
        App.get_running_app().stop()

    def on_pre_enter(self, *args):
        """화면 들어올 때 초기화 작업 (한 번만)"""
        if not self.regions:
            # 초기 지역 생성
            region_names = [
                "평안북도", "평안남도", "함경북도", "함경남도", "황해도",
                "강원도", "경기도", "경상남도", "경상북도", "전라남도",
                "전라북도", "충청북도", "충청남도", "제주도"
            ]
            ai_name_candidates = AI_NAMES[:]
            
            for name in region_names:
                self.regions[name] = Region(name, owner=None)
            
            # 플레이어가 선택한 지역 소유자 = 플레이어 이름
            if self.player_region_name:
                self.regions[self.player_region_name].owner = self.player_name
                # 자원 보너스
                self.regions[self.player_region_name].gold = 2000
                self.regions[self.player_region_name].food = 5000
                self.regions[self.player_region_name].population = 1500
            
            # 나머지 지역은 랜덤 AI 이름 부여
            for r_name, r_obj in self.regions.items():
                if r_obj.owner is None:
                    if len(ai_name_candidates) == 0:
                        ai_name_candidates = AI_NAMES[:]
                    r_obj.owner = random.choice(ai_name_candidates)
        
        # 시작 시, 선택된 땅 초기화
        self.selected_region_name = None
        self.selected_region_index = 0
        
        self.update_regions_info()
    
    # ----------------------------------
    # 플레이어가 소유한 땅 중 선택
    # ----------------------------------
    def select_owned_region_action(self, instance):
        """
        '땅 선택' 버튼을 누를 때마다
        플레이어가 소유한 지역 리스트를 순환하며 현재 선택 지역을 변경.
        """
        owned_regions = [r for r in self.regions.values() if r.owner == self.player_name]
        if not owned_regions:
            self.selected_region_name = None
            self.info_label.text = "플레이어가 소유한 지역이 없습니다."
            return
        
        # 인덱스를 지역 개수 안에서 순환
        self.selected_region_index = self.selected_region_index % len(owned_regions)
        region_obj = owned_regions[self.selected_region_index]
        self.selected_region_name = region_obj.name
        
        self.info_label.text = f"선택된 내 땅: {region_obj.name}"
        
        # 다음 버튼 누를 때는 다음 인덱스
        self.selected_region_index += 1
    
    def get_selected_region(self):
        """
        현재 선택된 내 지역 객체를 반환.
        만약 선택이 안 되어 있거나, 소유지가 없으면 None
        """
        if not self.selected_region_name:
            return None
        r_obj = self.regions.get(self.selected_region_name)
        if not r_obj:
            return None
        if r_obj.owner != self.player_name:
            return None
        return r_obj
    
    # ----------------------------------
    # 투자 버튼들
    # ----------------------------------


    def update_regions_info(self):
        """지역 정보를 갱신하여 스크롤뷰에 표시"""
        # 기존 정보 제거
        self.regions_layout.clear_widgets()
        
        for r_name, r_obj in self.regions.items():
            # 지역 이름
            region_label = Label(
                text=f"[{r_name}]\n소유자: {r_obj.owner}\n"
                     f"Gold: {r_obj.gold}\nFood: {r_obj.food}\n"
                     f"Population: {r_obj.population}\n"
                     f"Agriculture: {r_obj.agri}, Commerce: {r_obj.commerce}, Security: {r_obj.security}\n"
                     f"Army: {r_obj.army}",
                size_hint_y=None,
                height=120,
                font_name="batang",
                halign="left",
                valign="top"
            )
            region_label.text_size = (self.width, None)  # 텍스트 정렬을 위해 필요
            self.regions_layout.add_widget(region_label)

    def invest_agri_action(self, instance):
        my_region = self.get_selected_region()
        if not my_region:
            self.info_label.text = "투자할 내 땅이 선택되지 않았습니다."
            return
        my_region.invest_agri()
        self.info_label.text = f"{my_region.name} 농업투자 진행"
        self.update_regions_info()
    
    def invest_commerce_action(self, instance):
        my_region = self.get_selected_region()
        if not my_region:
            self.info_label.text = "투자할 내 땅이 선택되지 않았습니다."
            return
        my_region.invest_commerce()
        self.info_label.text = f"{my_region.name} 상업투자 진행"
        self.update_regions_info()
    
    def invest_security_action(self, instance):
        my_region = self.get_selected_region()
        if not my_region:
            self.info_label.text = "투자할 내 땅이 선택되지 않았습니다."
            return
        my_region.invest_security()
        self.info_label.text = f"{my_region.name} 치안투자 진행"
        self.update_regions_info()
    
    # ----------------------------------
    # 모병
    # ----------------------------------
    def recruit_action(self, instance):
        my_region = self.get_selected_region()
        if not my_region:
            self.info_label.text = "모병할 내 땅이 선택되지 않았습니다."
            return
        
        recruit_amount = 10  # 예시로 10명
        my_region.recruit_army(recruit_amount)
        self.info_label.text = f"{my_region.name}에서 병사 {recruit_amount}명 모집"
        
        self.update_regions_info()
    
    # ----------------------------------
    # 공격
    # ----------------------------------
    def attack_action(self, instance):
        my_region = self.get_selected_region()
        if not my_region:
            self.info_label.text = "공격할 내 땅이 선택되지 않았습니다."
            return
        
        # 인접 지역 중에서 적 소유 찾기
        neighbors = REGION_ADJACENCY.get(my_region.name, [])
        enemy_regions = []
        for nb_name in neighbors:
            if self.regions[nb_name].owner != self.player_name:
                enemy_regions.append(self.regions[nb_name])
        
        if not enemy_regions:
            self.info_label.text = f"{my_region.name} 인접에 적 소유 지역 없음"
            return
        
        # 임시로 첫 번째 적 지역만 공격
        target_region = enemy_regions[0]
        
        # 무작위로 점령/약탈 (실제로는 UI로 선택)
        mode = random.choice(["occupy", "plunder"])
        
        attacker_soldiers = my_region.army
        if attacker_soldiers <= 0:
            self.info_label.text = "병력이 없습니다. 공격 불가!"
            return
        
        defender_soldiers = target_region.army
        
        att_after, def_after = do_battle_attack(attacker_soldiers, defender_soldiers)
        my_region.army = att_after
        target_region.army = def_after
        
        if att_after > 0 and def_after == 0:
            # 승리
            if mode == "occupy":
                old_owner = target_region.owner
                target_region.owner = self.player_name
                self.info_label.text = (
                    f"[점령 성공]\n{my_region.name} → {target_region.name} (소유자:{old_owner} -> {self.player_name})"
                )
            else:
                # 약탈
                stolen_gold = int(target_region.gold * 0.5)
                stolen_food = int(target_region.food * 0.5)
                target_region.gold -= stolen_gold
                target_region.food -= stolen_food
                target_region.security = int(target_region.security * 0.5)
                
                my_region.gold += stolen_gold
                my_region.food += stolen_food
                
                self.info_label.text = (
                    f"[약탈 성공]\n{my_region.name} -> {target_region.name}\n"
                    f"금 {stolen_gold}, 식량 {stolen_food} 약탈\n"
                    f"{target_region.name} 치안 50% 감소"
                )
        else:
            # 실패 또는 서로 생존(수비 승)
            self.info_label.text = f"[공격 실패]\n공격군 생존:{att_after}, 수비군 생존:{def_after}"
        
        self.update_regions_info()
    
    # ----------------------------------
    # 저장
    # ----------------------------------
    def save_game(self, instance):
        data = {
            "player_name": self.player_name,
            "player_region_name": self.player_region_name,
            "regions": {}
        }
        
        for r_name, r_obj in self.regions.items():
            data["regions"][r_name] = {
                "owner": r_obj.owner,
                "gold": r_obj.gold,
                "food": r_obj.food,
                "population": r_obj.population,
                "agri": r_obj.agri,
                "commerce": r_obj.commerce,
                "security": r_obj.security,
                "army": r_obj.army
            }
        
        with open("savefile.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.info_label.text = "게임이 저장되었습니다."
    
    # ----------------------------------
    # 턴 종료
    # ----------------------------------
    def next_turn(self, instance):
        # 1) 모든 지역 자원 갱신
        for r_obj in self.regions.values():
            r_obj.next_turn()
        
        # 2) AI 로직
        for r_obj in self.regions.values():
            if r_obj.owner == self.player_name:
                continue
            
            # 자원이 충분하면 투자 or 모병
            if r_obj.gold > 2000:
                action = random.choice(["agri", "commerce", "security"])
                if action == "agri":
                    r_obj.invest_agri()
                elif action == "commerce":
                    r_obj.invest_commerce()
                else:
                    r_obj.invest_security()
            elif r_obj.food > 2000 and r_obj.population > 1100:
                r_obj.recruit_army(random.randint(5, 20))
        
        self.update_regions_info()
        self.info_label.text = "다음 턴이 시작되었습니다."

# ----------------------
# 불러오기 스크린
# ----------------------
class LoadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        load_btn = Button(text="파일 불러오기", font_name="batang")
        load_btn.bind(on_release=self.load_game_file)
        
        self.info_label = Label(text="저장된 파일을 불러옵니다.", font_name="batang")
        
        layout.add_widget(self.info_label)
        layout.add_widget(load_btn)
        
        self.add_widget(layout)
    
    def load_game_file(self, instance):
        if not os.path.exists("savefile.json"):
            self.info_label.text = "세이브 파일이 없습니다."
            return
        
        with open("savefile.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        game_screen = self.manager.get_screen("game")
        game_screen.player_name = data["player_name"]
        game_screen.player_region_name = data["player_region_name"]
        
        for r_name, r_data in data["regions"].items():
            if r_name not in game_screen.regions:
                game_screen.regions[r_name] = Region(r_name)
            
            r_obj = game_screen.regions[r_name]
            r_obj.owner = r_data["owner"]
            r_obj.gold = r_data["gold"]
            r_obj.food = r_data["food"]
            r_obj.population = r_data["population"]
            r_obj.agri = r_data["agri"]
            r_obj.commerce = r_data["commerce"]
            r_obj.security = r_data["security"]
            r_obj.army = r_data["army"]
        
        self.manager.current = "game"

# ----------------------
# 설정 스크린 (단순 예시)
# ----------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        label = Label(text="설정 화면입니다.", font_name="batang")
        back_btn = Button(text="뒤로가기", font_name="batang")
        back_btn.bind(on_release=self.go_back)
        
        layout.add_widget(label)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def go_back(self, instance):
        self.manager.current = "main"

# ----------------------
# ScreenManager
# ----------------------
class HangukGameApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main"))
        sm.add_widget(StartRegionScreen(name="startregion"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(LoadScreen(name="load"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

# ----------------------
# 메인 실행
# ----------------------
if __name__ == "__main__":
    HangukGameApp().run()
