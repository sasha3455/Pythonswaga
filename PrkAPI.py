import aiohttp
import asyncio
from datetime import datetime
import json
import os

API_KEY_CALORIES = 'JCLE1V9G4MgVpFZ96nYJcg==bvsshk4fe5AuXyCM'
API_KEY_EXERCISES = 'JCLE1V9G4MgVpFZ96nYJcg==bvsshk4fe5AuXyCM'
HISTORY_FILE = 'activity_history.json'

activity_translate = {
    'бег': 'running',
    'ходьба': 'walking',
    'велосипед': 'cycling',
    'плавание': 'swimming',
    'йога': 'yoga',
    'прыжки': 'jumping jacks',
    'приседания': 'squats',
    'отжимания': 'push-ups',
    'скакалка': 'jump rope',
    'гребля': 'rowing',
    'танцы': 'dancing',
    'подъем по лестнице': 'stair climbing'
}

class ActivityTracker:
    def __init__(self):
        self.history = self.load_history()
    
    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def save_history(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_activity(self, activity_data):
        self.history.append(activity_data)
        self.save_history()
    
    def get_stats(self):
        total_calories = sum(act['total_calories'] for act in self.history)
        total_minutes = sum(act['duration_minutes'] for act in self.history)
        return {
            'total_activities': len(self.history),
            'total_calories': total_calories,
            'total_minutes': total_minutes,
            'avg_calories_per_activity': total_calories / len(self.history) if self.history else 0
        }

async def get_calories_burned(session, activity, weight=None, duration=None):
    api_url = 'https://api.api-ninjas.com/v1/caloriesburned'
    params = {'activity': activity}
    
    if weight:
        params['weight'] = weight
    if duration:
        params['duration'] = duration
    
    async with session.get(api_url, headers={'X-Api-Key': API_KEY_CALORIES}, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data[0] if data else None
        else:
            print(f"[ERROR] API калорий: {response.status} — {await response.text()}")
            return None

async def get_exercise_info(session, activity):
    api_url = 'https://api.api-ninjas.com/v1/exercises'
    params = {'name': activity}
    
    async with session.get(api_url, headers={'X-Api-Key': API_KEY_EXERCISES}, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data[0] if data else None
        else:
            print(f"[ERROR] API упражнений: {response.status} — {await response.text()}")
            return None

async def track_activity(tracker, activity, weight=None, duration=None):
    async with aiohttp.ClientSession() as session:
        calories_data, exercise_info = await asyncio.gather(
            get_calories_burned(session, activity, weight, duration),
            get_exercise_info(session, activity)
        )
        
        if not calories_data:
            print("Не удалось получить данные о калориях.")
            return
        
        activity_data = {
            'activity': calories_data['name'],
            'calories_per_hour': calories_data['calories_per_hour'],
            'duration_minutes': calories_data['duration_minutes'],
            'total_calories': calories_data['total_calories'],
            'weight': weight,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'exercise_info': exercise_info
        }
        
        tracker.add_activity(activity_data)
        return activity_data

def display_activity(activity_data):
    print("\n" + "="*50)
    print(f"Активность: {activity_data['activity']}")
    print(f"Дата: {activity_data['date']}")
    print(f"Продолжительность: {activity_data['duration_minutes']} мин")
    print(f"Сожжено калорий: {activity_data['total_calories']}")
    
    if activity_data['exercise_info']:
        print("\nИнформация об упражнении:")
        print(f"Тип: {activity_data['exercise_info'].get('type', 'N/A')}")
        print(f"Мышцы: {activity_data['exercise_info'].get('muscle', 'N/A')}")
        print(f"Оборудование: {activity_data['exercise_info'].get('equipment', 'N/A')}")
        print(f"Сложность: {activity_data['exercise_info'].get('difficulty', 'N/A')}")

def display_stats(stats):
    print("\n" + " "*50)
    print("СТАТИСТИКА АКТИВНОСТИ")
    print(" "*50)
    print(f"Всего активностей: {stats['total_activities']}")
    print(f"Общее время: {stats['total_minutes']} мин ({stats['total_minutes']//60} ч {stats['total_minutes']%60} мин)")
    print(f"Всего сожжено калорий: {stats['total_calories']}")
    print(f"Среднее калорий за активность: {stats['avg_calories_per_activity']:.1f}")

async def main():
    tracker = ActivityTracker()
    
    while True:
        print("\nМеню:")
        print("1. Добавить активность")
        print("2. Показать историю")
        print("3. Показать статистику")
        print("4. Выход")
        
        choice = input("Выберите действие: ")
        
        if choice == '1':
            activity = input("Введите активность: ").strip().lower()
            activity = activity_translate.get(activity, activity)
            
            weight_input = input("Введите вес (кг, опционально): ")
            duration_input = input("Введите продолжительность (мин, опционально): ")

            if weight_input:
                try:
                    weight = int(weight_input)
                    if weight < 50 or weight > 500:
                        print("Вес должен быть от 50 до 500 кг.")
                        continue
                except ValueError:
                    print("Неверный формат веса.")
                    continue
            else:
                weight = None

            try:
                duration = int(duration_input) if duration_input else 60
            except ValueError:
                print("Неверный формат продолжительности.")
                continue

            activity_data = await track_activity(tracker, activity, weight, duration)
            if activity_data:
                display_activity(activity_data)
        
        elif choice == '2':
            print("\nИстория активностей:")
            for i, act in enumerate(tracker.history, 1):
                print(f"{i}. {act['date']} - {act['activity']} ({act['duration_minutes']} мин, {act['total_calories']} кал)")
        
        elif choice == '3':
            stats = tracker.get_stats()
            display_stats(stats)
        
        elif choice == '4':
            print("Выход из программы.")
            break
        
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    asyncio.run(main())
