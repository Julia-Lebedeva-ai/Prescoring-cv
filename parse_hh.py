import requests
from bs4 import BeautifulSoup
import json
import re 

def get_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def extract_candidate_data(html_content):
    """
    Извлекает данные кандидата из HTML страницы SuperJob.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Отладка: посмотрим, какие script теги есть
    script_tags = soup.find_all('script')
    print(f"Найдено script тегов в SuperJob: {len(script_tags)}")
    
    # Ищем script теги с данными
    data_scripts = []
    for i, script in enumerate(script_tags[:5]):  # Посмотрим первые 5
        if script.string:
            content = script.string[:100] if len(script.string) > 100 else script.string
            print(f"Script {i}: {content}...")
            if 'data' in script.string or 'resume' in script.string.lower():
                data_scripts.append(script)
    
    # Пробуем найти данные в разных форматах
    for script in data_scripts:
        try:
            script_text = script.string
            # Ищем JSON данные
            if '{' in script_text and '}' in script_text:
                # Пробуем найти начало и конец JSON
                start = script_text.find('{')
                end = script_text.rfind('}') + 1
                
                if start != -1 and end != -1:
                    json_str = script_text[start:end]
                    data = json.loads(json_str)
                    
                    # Пробуем найти резюме данные в разных местах
                    if isinstance(data, dict):
                        # Вариант 1: данные в корне
                        if 'position' in data or 'salary' in data:
                            # Формируем простой вывод
                            markdown = f"""
# Резюме кандидата (SuperJob)

## Основная информация
- **Должность:** {data.get('position', 'Не указана')}
- **Зарплата:** {data.get('salary', 'Не указана')}
"""
                            return markdown.strip()
                        
                        # Вариант 2: ищем вложенные структуры
                        for key, value in data.items():
                            if isinstance(value, dict) and ('position' in value or 'title' in value):
                                markdown = f"""
# Резюме кандидата (SuperJob)

## Найденные данные
"""
                                for k, v in value.items():
                                    if isinstance(v, (str, int, float)):
                                        markdown += f"- **{k}:** {v}\n"
                                return markdown.strip()
        except Exception as e:
            continue
    
    # Если ничего не нашли в script тегах, попробуем извлечь данные из HTML
    try:
        # Извлечение основных данных из HTML
        position_elem = soup.find('h1')
        position = position_elem.text.strip() if position_elem else 'Не указана'
        
        # Зарплата
        salary_elem = soup.find(string=re.compile(r'руб|RUB|₽', re.I))
        salary = salary_elem.strip() if salary_elem else 'Не указана'
        
        # Опыт
        experience_elems = soup.find_all(string=re.compile(r'опыт|стаж|experience', re.I))
        experience = experience_elems[0].strip() if experience_elems else 'Не указан'
        
        markdown = f"""
# Резюме кандидата (SuperJob)

## Основная информация (из HTML)
- **Должность:** {position}
- **Зарплата:** {salary}
- **Опыт:** {experience}
"""
        
        return markdown.strip()
    except Exception as e:
        return f"Данные кандидата не найдены. Ошибка: {str(e)}"

def extract_vacancy_data(html_content):
    """
    Извлекает данные вакансии из HTML страницы HH.ru.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Отладка: посмотрим, какие script теги есть
    script_tags = soup.find_all('script')
    print(f"Найдено script тегов в HH.ru: {len(script_tags)}")
    
    # Ищем script теги с данными вакансии
    for i, script in enumerate(script_tags[:10]):  # Посмотрим первые 10
        if script.string:
            content = script.string[:200] if len(script.string) > 200 else script.string
            if 'vacancy' in script.string.lower() or 'HH' in script.string:
                print(f"Script {i} (вакансия): {content}...")
                break
    
    # Пробуем найти данные в теге с типом application/ld+json
    ld_json_script = soup.find('script', type='application/ld+json')
    if ld_json_script and ld_json_script.string:
        try:
            data = json.loads(ld_json_script.string)
            if '@type' in data and data['@type'] == 'JobPosting':
                title = data.get('title', 'Не указана')
                company = data.get('hiringOrganization', {}).get('name', 'Не указана')
                description = data.get('description', 'Не указано')
                
                # Очистка описания
                if description:
                    description = re.sub(r'<[^>]+>', '', description)
                    description = description.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&')
                
                markdown = f"""
# {title}

## Основная информация (JSON-LD)
- **Компания:** {company}
- **Описание:** {description[:500]}...""" if len(description) > 500 else description

                return markdown.strip()
        except:
            pass
    
    # Пробуем извлечь данные из HTML структуры
    try:
        # Заголовок вакансии
        title_elem = soup.find('h1', {'data-qa': 'vacancy-title'})
        title = title_elem.text.strip() if title_elem else 'Не указана'
        
        # Зарплата
        salary_elem = soup.find('div', {'data-qa': 'vacancy-salary'})
        salary = salary_elem.text.strip() if salary_elem else 'Не указана'
        
        # Компания
        company_elem = soup.find('a', {'data-qa': 'vacancy-company-name'})
        company = company_elem.text.strip() if company_elem else 'Не указана'
        
        # Опыт
        experience_elem = soup.find(string=re.compile(r'опыт', re.I))
        experience = experience_elem.strip() if experience_elem else 'Не указан'
        
        # Описание
        description_elem = soup.find('div', {'data-qa': 'vacancy-description'})
        description = description_elem.text.strip() if description_elem else 'Не указано'
        
        # Навыки
        skills_elem = soup.find('div', {'class': 'bloko-tag-list'})
        skills = []
        if skills_elem:
            skill_tags = skills_elem.find_all('span', {'class': 'bloko-tag__section_text'})
            skills = [tag.text.strip() for tag in skill_tags]
        
        markdown = f"""
# {title}

## Основная информация (HTML)
- **Компания:** {company}
- **Зарплата:** {salary}
- **Требуемый опыт:** {experience}

## Описание
{description[:1000]}...""" if len(description) > 1000 else description

        if skills:
            markdown += "\n\n## Навыки\n"
            for skill in skills[:10]:
                markdown += f"- {skill}\n"
        
        return markdown.strip()
    except Exception as e:
        return f"Данные вакансии не найдены. Ошибка: {str(e)}"

# Тестируем
'''vac_html = get_html('https://hh.ru/vacancy/129478614?from=applicant_recommended&hhtmFrom=main')
cv_html = get_html('https://voronezh.superjob.ru/resume/menedzher-proektov-5761863.html?fromSearch=true')

print("=" * 50)
vac = extract_vacancy_data(vac_html)
print("=" * 50)
cv = extract_candidate_data(cv_html)
print("=" * 50)

print(f"\nВакансия:\n{vac}")
print(f"\n" + "="*50)
print(f"\nРезюме:\n{cv}")'''