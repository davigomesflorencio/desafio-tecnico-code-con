from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import date
import time
from collections import Counter,defaultdict
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()

# Armazenamento em cache (na memória)
cache = {}

# Modelos de dados
class Project(BaseModel):
    nome: str
    concluido: bool

class Team(BaseModel):
    nome: str
    lider: bool
    projetos: List[Project]

class LogEntry(BaseModel):
    data: date
    acao: str

class Person(BaseModel):
    id: UUID4
    nome: str
    idade: int
    score: int
    ativo: bool
    pais: str
    equipe: Team
    logs: List[LogEntry]
    
@app.post("/users")
def read_root(people: List[Person]):
    cache["people"] = [person.model_dump() for person in people]
    return {"message": f"{len(people)} pessoas armazenadas em cache"}

@app.get("/users")
def read_root():
    if "people" not in cache:
        raise HTTPException(status_code=404, detail="Nenhuma pessoa em cache")
    start_time = time.time() 
   
    superusers = [
        person for person in cache["people"]
        if person["score"] >= 900 and person["ativo"]
    ]
    
    end_time = time.time()  # ⏱️ Fim da contagem
    processing_time_ms = round((end_time - start_time) * 1000, 2)


    return {
        "processing_time_ms": processing_time_ms,
        "total": len(superusers),
        "data": superusers
    }

@app.get("/top-countries")
def read_root():
    if "people" not in cache:
        raise HTTPException(status_code=404, detail="Nenhuma pessoa em cache")
    
    start_time = time.time() 
   
    superusuarios = [usuario["pais"] for usuario in cache["people"] if usuario["score"] > 800]
    
    # Contando o número de superusuários por país
    pais_contagem = Counter(superusuarios)
    
    # Ordenando por quantidade e pegando os 5 principais
    top_5_paises = pais_contagem.most_common(5)
    
    end_time = time.time()  # ⏱️ Fim da contagem
    processing_time_ms = round((end_time - start_time) * 1000, 2)


    return {
        "processing_time_ms": processing_time_ms,
        "total": len(top_5_paises),
        "data": top_5_paises
    }

@app.get("/team-insights")
def read_root():
    if "people" not in cache:
        raise HTTPException(status_code=404, detail="Nenhuma pessoa em cache")
    
    start_time = time.time() 
   
    team_data = defaultdict(lambda: {"total_membros": 0, "lideres": 0, "projetos_concluidos": 0, "ativos": 0})
    
    for usuario in cache["people"]:
        equipe = usuario["equipe"]
        team_info = team_data[equipe["nome"]]
        
        # Contando membros e líderes
        team_info["total_membros"] += 1
        if equipe["lider"]:
            team_info["lideres"] += 1
        
        # Contando projetos concluídos
        team_info["projetos_concluidos"] += sum(1 for p in equipe["projetos"] if p["concluido"])
        
        # Contando membros ativos
        if usuario["ativo"]:
            team_info["ativos"] += 1

    insights = []
    for team_name, data in team_data.items():
        porcentagem_ativos = (data["ativos"] / data["total_membros"]) * 100 if data["total_membros"] > 0 else 0
        insights.append({
            "team_name": team_name,
            "total_membros": data["total_membros"],
            "lideres": data["lideres"],
            "projetos_concluidos": data["projetos_concluidos"],
            "percentagem_ativos": round(porcentagem_ativos, 2)
        })
    
    end_time = time.time()  # ⏱️ Fim da contagem
    processing_time_ms = round((end_time - start_time) * 1000, 2)

    return {
        "processing_time_ms": processing_time_ms,
        "total": len(insights),
        "data": insights
    }

@app.get("/active-users-per-day")
def read_root(min: Optional[int] = Query(None, ge=0)):
    if "people" not in cache:
        raise HTTPException(status_code=404, detail="Nenhuma pessoa em cache")
    
    start_time = time.time() 
    
    login_count_by_day = defaultdict(int)
    
    for usuario in cache['people']:
        for log in usuario["logs"]:
            if log["acao"] == "login":
                login_count_by_day[log["data"]] += 1

    if min is not None:
        login_count_by_day = {date: count for date, count in login_count_by_day.items() if count >= min}

    active_users_per_day = [{"data": date, "logins": count} for date, count in login_count_by_day.items()]

    end_time = time.time()
    processing_time_ms = round((end_time - start_time) * 1000, 2)


    return {
        "processing_time_ms": processing_time_ms,
        "total": len(active_users_per_day),
        "data": active_users_per_day
    }

def test_endpoint(url: str) -> dict:
    client = TestClient(app)
    start_time = time.time()
    
    try:
        response =  client.get(url)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        status_ok = response.status_code == 200
        
        try:
            response_json = response.json()
            json_valid = True
        except ValueError:
            json_valid = False
        
        return {
            "status_code": response.status_code,
            "status_ok": status_ok,
            "time_ms": round(response_time_ms, 2),
            "valid_response": json_valid
        }
    
    except Exception as e:
        return {
            "status_code": None,
            "status_ok": False,
            "time_ms": None,
            "valid_response": False,
            "error": str(e)
        }

@app.get("/evaluation")
async def evaluation():
    endpoints = [
        "/users",
        "/top-countries",
        "/team-insights",
        "/active-users-per-day"
    ]
    codeStatus =200 
    
    results = {}
    for endpoint in endpoints:
        url = f"http://127.0.0.1:8000{endpoint}"
        result = test_endpoint(url)
        if(result["status_code"]!=200):
            codeStatus = result["status_code"]
        results["/"+url.split("/")[-1]] = result
    
    return JSONResponse(
        content={
            "descricao": "Executa testes automáticos nos endpoints da própria API e retorna um relatório de pontuação.",
            "response": {
                "status":codeStatus,
                "body":{
                    "tested_endpoints": results
                }
            },
        }
        )