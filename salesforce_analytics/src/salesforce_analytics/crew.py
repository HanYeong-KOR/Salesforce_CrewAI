from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from .tools.salesforce_connection_tool import SalesforceExtractTool

load_dotenv()

llm = ChatOpenAI(model=os.getenv('MODEL'), openai_api_key=os.getenv('OPENAI_API_KEY'))

OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'outputs'))  # 절대 경로로 변경


@CrewBase
class SalesforceCrewai():
    """SalesforceCrewai crew"""

    def __init__(self):
        # 모든 outputs 디렉토리 미리 생성 (절대 경로)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'salesforce_connector'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'data_analyzer'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'summary_generator'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'translator'), exist_ok=True)
        os.makedirs(os.path.join(OUTPUTS_DIR, 'report_creator'), exist_ok=True)

        # Salesforce Tool 인스턴스
        self.salesforce_tool = SalesforceExtractTool()

    @agent
    def salesforce_connector(self) -> Agent:
        return Agent(
            config=self.agents_config['salesforce_connector'],
            llm=llm,
            tools=[self.salesforce_tool],
            verbose=True
        )

    @agent
    def data_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyzer'],
            llm=llm,
            verbose=True
        )

    @agent
    def summary_generator(self) -> Agent:
        return Agent(config=self.agents_config['summary_generator'], llm=llm, verbose=True)

    @agent
    def translator(self) -> Agent:
        return Agent(config=self.agents_config['translator'], llm=llm, verbose=True)

    @agent
    def report_creator(self) -> Agent:
        return Agent(config=self.agents_config['report_creator'], llm=llm, verbose=True)

    @task
    def data_extract_task(self) -> Task:
        config = self.tasks_config['data_extract_task'].copy()
        config['output_file'] = os.path.join(OUTPUTS_DIR, 'salesforce_connector',
                                             f'extracted_data_{datetime.now().year}.csv')
        return Task(**config)

    @task
    def data_analysis_task(self) -> Task:
        config = self.tasks_config['data_analysis_task'].copy()
        config['output_file'] = os.path.join(OUTPUTS_DIR, 'data_analyzer',
                                             f'analysis_results_{datetime.now().year}.json')
        return Task(**config)

    @task
    def summary_generation_task(self) -> Task:
        config = self.tasks_config['summary_generation_task'].copy()
        config['output_file'] = os.path.join(OUTPUTS_DIR, 'summary_generator', f'summary_{datetime.now().year}.md')
        return Task(**config)

    @task
    def translation_task(self) -> Task:
        config = self.tasks_config['translation_task'].copy()
        config['output_file'] = os.path.join(OUTPUTS_DIR, 'translator', f'translated_summary_{datetime.now().year}.md')
        return Task(**config)

    @task
    def report_creation_task(self) -> Task:
        config = self.tasks_config['report_creation_task'].copy()
        config['output_file'] = os.path.join(OUTPUTS_DIR, 'report_creator',
                                             f'salesforce_{datetime.now().year}_summary_report.pdf')
        return Task(**config)

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.salesforce_connector(), self.data_analyzer(), self.summary_generator(), self.translator(),
                    self.report_creator()],
            tasks=[self.data_extract_task(), self.data_analysis_task(), self.summary_generation_task(),
                   self.translation_task(), self.report_creation_task()],
            process=Process.sequential
        )

    def run(self, inputs=None):
        try:
            result = self.crew().kickoff(inputs=inputs or {})
            print(f"Crew completed: {result}")
            return result
        except Exception as e:
            print(f"Error in Crew execution: {str(e)}")
            raise