import os
import glob
import time
import pickle
import numpy as np
import traceback
from multiprocessing import Process, Value, Manager
import google.generativeai as genai
from openai import OpenAI
import re
import pandas as pd
import ast

def simplify_sentences_gpt(sentences, prompt_text, modelname='gpt-4.1-nano', temperature=0):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        messages = [{"role": "user", "content": prompt_text + ' ' + str(sentences)}]
        
        response = client.chat.completions.create(
            model = modelname,
            messages = messages,
            temperature = temperature
        )
        content = response.choices[0].message.content.strip()

        try:
            content_c = content.replace('```', '')
            simplified = ast.literal_eval(content_c)

        except Exception as e:
            content_wo_brackets = content_c.replace('[', '').replace(']', '')
            simplified = [
                re.sub(r"^\s*(?:[\d]+|[-–])[\.\)-]?\s*'\"`", "", line).strip()
                for line in content_wo_brackets.splitlines()
                if line.strip()
            ]
            
        if len(sentences) + 1 == len(simplified):
            simplified = simplified[1:]

    except Exception as e:
        print(f"[ERROR] OpenAI API call failed: {e}")
        return simplified, True

    if len(simplified) != len(sentences):
        print(f"[WARNING] Mismatch: {len(sentences)} input vs {len(simplified)} output")
        return simplified, True

    return simplified, False

def simplify_sentences_gemini(sentences, prompt_text, modelname='gemini-2.0-flash', temperature=0):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    gemini_model = genai.GenerativeModel(modelname)

    try:
        messages = [{"role": "user", "parts": prompt_text + ' ' + str(sentences)}]
        
        completion = gemini_model.generate_content(
            generation_config = genai.types.GenerationConfig(temperature=temperature),
            contents = messages
        )
        content = completion.text.strip()

        try:
            content_c = content.replace('```', '')
            simplified = ast.literal_eval(content_c)

        except Exception as e:
            content_wo_brackets = content_c.replace('[', '').replace(']', '')
            simplified = [
                re.sub(r"^\s*(?:[\d]+|[-–])[\.\)-]?\s*'\"`", "", line).strip()
                for line in content_wo_brackets.splitlines()
                if line.strip()
            ]
            
        if len(sentences) + 1 == len(simplified):
            simplified = simplified[1:]

    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return simplified, True

    if len(simplified) != len(sentences):
        print(f"[WARNING] Mismatch: {len(sentences)} input vs {len(simplified)} output")
        return simplified, True

    return simplified, False

def do_llm_call(df_chunk, snts_done, p_id, run_id, prompt_text, run_chatgpt, modelname, snts_broken):
    try:
        save_path = f"./simplified_chunks/{run_id}"
        os.makedirs(save_path, exist_ok=True)

        if 'prep_snt' not in df_chunk:
            df_chunk = df_chunk.T
            
        sentences = df_chunk["prep_snt"].tolist()
        snts_id = df_chunk.index.tolist()

        if run_chatgpt: 
            simplified_sents, had_error = simplify_sentences_gpt(sentences, prompt_text, modelname)
        else:
            simplified_sents, had_error = simplify_sentences_gemini(sentences, prompt_text, modelname)

        if not had_error:
            result = [(snts_id[i], simplified_sents[i]) for i in range(len(simplified_sents))]

            with open(f"{save_path}/snts_{p_id}.pkl", "wb") as f:
                pickle.dump(result, f)

            with snts_done.get_lock():
                snts_done.value += len(df_chunk)
        else:
            for s_id in snts_id:
                snts_broken.append(s_id)
    except Exception as e:
        print(f"\n[ERROR] Process {p_id} failed:")
        traceback.print_exc()

def get_chunk_ids(df, parts):
    ids = np.random.RandomState(seed=42).permutation(df.index)
    return np.array_split(ids, parts)

def run_parallel_simplification_w_llm(df, run_id, prompt_text, run_chatgpt, modelname, parts=10):
    df = df.reset_index(drop=True)
    chunk_ids = get_chunk_ids(df, parts)
    snts_done = Value("i", 0)
    
    manager = Manager()
    snts_broken = manager.list()
    
    processes = []

    for p_id, chunk_id in enumerate(chunk_ids):
        chunk = df.iloc[chunk_id]
        proc = Process(target=do_llm_call, args=(chunk, snts_done, p_id, run_id, prompt_text[0], run_chatgpt, modelname, snts_broken))
        processes.append(proc)
        proc.start()
        time.sleep(2)
    for proc in processes:
        proc.join()
    
    # handle remaining broken sentences
    shuffled_broken_ids = np.random.RandomState(seed=42).permutation(list(snts_broken))
    snts_broken = manager.list()

    for i in shuffled_broken_ids:
        chunk = df.iloc[i]
        proc = Process(target=do_llm_call, args=(pd.DataFrame(chunk), snts_done, len(df) + i, run_id, prompt_text[1], run_chatgpt, modelname, snts_broken))
        processes.append(proc)
        proc.start()
        time.sleep(2)
    for proc in processes:
        proc.join()

def load_simplified_results(run_id):
    files = sorted(glob.glob(f"./simplified_chunks/{run_id}/snts_*.pkl"))
    results = []
    for fpath in files:
        with open(fpath, "rb") as f:
            chunk_data = pickle.load(f)
            results.extend(chunk_data)
    print(f"total sentences: {len(results)}")
    return results
