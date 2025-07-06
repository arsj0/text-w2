from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from ollama import ListResponse, list
from langchain_openai import ChatOpenAI
import lmstudio as lms
from utils import app_config
from typing import List

class llmService:

    lms_prefix = "[lms] "

    class Translation_structure (BaseModel):
        """ For structured output, perform translation of user's input """
        output_lang: str = Field(description="Name of the targeted output language")
        translation_output: str = Field(description="the output of translation")

    def lms_get_model_list(self): 
        """ return the model list in lmStudio """ 
        model_list = []

        try:
            llm_only = lms.list_downloaded_models("llm")
            for model in llm_only:
                model_list.append(self.lms_prefix + model.model_key)

        except:
            print("starting with no lmStudio")

        return model_list


    def ollama_get_model_list(self): 
        """ return the model list in ollama """
        model_list = []
        try:
            response: ListResponse = list()
            
            for model in response.models:
                model_list.append(model.model)
        except:
            print("starting with no ollama.")
 
        return model_list

    def llm_serve(self, model_name, ollama_num_ctx, tempreature):
        """ Define llm for translation service """
        llm = None

        if (model_name.startswith(self.lms_prefix)):
            model_name = model_name.replace(self.lms_prefix, "", 1)
            llm = ChatOpenAI(
                base_url = app_config.LM_STUDIO_URL,
                api_key = 'lm-studio',
                model = model_name,
                temperature=tempreature
            )
        else:

            llm = ChatOllama(
                model=model_name,
                num_ctx=ollama_num_ctx,
                temperature=tempreature
            )
             
        return llm

    def llm_translate(self, model_name ,ipt_lang, opt_lang, ipt_content, ref_content = None):
        """ agent: translate """

        # handle ref content
        if (ref_content):
            ref_str = '\n'.join(ref_content[-40:])
            ref_str = " If any, i will provide up to the lastest 40 lines for your reference and better understanding on the current ongoing script. Do NOT include them in ur output. <reference>" +  ref_str + "</reference>"
        else:
            ref_str = ""

        llm = self.llm_serve(model_name, 30000, 0.4)

        structured_llm = llm.with_structured_output(self.Translation_structure)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant that translates a srt script line by line, from mainly {input_language} to {output_language}. {ref_msg} no_think ",
                ),
                ("human", "input: {user_input}"),
            ]
        )

        chain = prompt | structured_llm
        chat = chain.invoke(
                {
                    "input_language": ipt_lang,
                    "output_language": opt_lang,
                    "user_input": ipt_content,
                    "ref_msg": ref_str,
                }
            )

        return chat.translation_output



    class sums_script_structure (BaseModel):
        """ For structured output, provide summary of user's input """
        output_lang: str = Field(description="Name of the output language")
        general_summary: str = Field(description="A short summary on what the sound track is about")
        #key_points: str = Field(description="List of the key points or takeaways from the sound track in point form, NO markdown format")


    def llm_sums_script(self, model_name, ipt_content, opt_lang):
        """ agent: summary of script """

        llm = self.llm_serve(model_name, 20000, 0.5)
        structured_llm = llm.with_structured_output(self.sums_script_structure)

        if(opt_lang): 
            output_language_prompt = "Please give ur response in language of " + opt_lang
        else:
            output_language_prompt = "Please give ur response in SAME language of the script" 

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You are a helpful assistant that provide summary on an audio sound track. User will provide the transcribed srt script of the audio to u.
                    Pls read and summarize it and provide structured output. {output_language}. no_think
                    """,
                ),
                ("human", "input: {user_input}"),
            ]
        )
 
        chain = prompt | structured_llm
        chat = chain.invoke(
                {
                    "output_language": output_language_prompt,
                    "user_input": ipt_content,
                }
            )
        
        return chat
