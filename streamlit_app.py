# streamlit run "/Users/julia/Developer/python/Zerocoder education/PE38 Prescoring CV/streamlit_app.py"
import streamlit as st
from openai import OpenAI
from parse_hh import get_html,extract_candidate_data,extract_vacancy_data

# Установите ваш API-ключ OpenAI

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
    base_url=st.secrets["base_url"],
)

system_prompt = """
Проскорь кандидата, насколько он подходит для данной вакансии.

Сначала напиши короткий анализ, который будет пояснять оценку.
Отдельно оцени качество заполнения резюме (понятно ли, с какими задачами сталкивался кандидат и каким образом их решал?). Эта оценка должна учитываться при выставлении финальной оценки - нам важно нанимать таких кандидатов, которые могут рассказать про свою работу
Потом представь результат в виде оценки от 1 до 10.
""".strip()

def get_openai_response(prompt,sys_prompt):
    try:
        # Отправляем запрос к OpenAI (например, GPT-3.5-turbo)
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
              {
                "role": "system",
                "content": sys_prompt
              },
              {
                "role": "user",
                "content": prompt,
              }
            ],
            max_tokens= 1000,
            temperature=0.7
        )
        # Извлекаем ответ
        return (response.choices[0].message.content)
    except Exception as e:
        return f"Произошла ошибка: {str(e)}"
    
st.title('CV Scoring App')
job_description = st.text_area('Введите ссылку на вакансию')
cv = st.text_area('Введите ссылку на резюме')
if st.button('Score CV'):
    with st.spinner('Scoring CV...'):
        try:
            job_html = get_html(job_description)
            resume_html = get_html(cv)
            job_text = extract_vacancy_data(job_html)
            resume_text = extract_candidate_data(resume_html)
            # Формирование пользовательского промпта
            user_prompt = f"# ВАКАНСИЯ\n{job_text}\n\n# РЕЗЮМЕ\n{resume_text}"
            # Отправляем запрос с системным и пользовательским промптами
            response = get_openai_response(system_prompt, user_prompt)
            st.subheader("📊 Результат анализа:")
            st.markdown(response)
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")