# Resumo Final do Projeto – Integração SCA com DefectDojo

## 1. Objetivo do Projeto

Este projeto teve como objetivo integrar ferramentas de **Software Composition Analysis (SCA)** num **pipeline CI/CD**, centralizando os resultados no **DefectDojo** para gestão e visualização de vulnerabilidades. A solução foi desenvolvida com **ferramentas open-source**, adequada a um contexto académico e alinhada com práticas **DevSecOps**.

---

## 2. Arquitetura Geral

* **GitHub Actions**: execução automática do pipeline
* **Ferramentas SCA**:

  * Trivy (filesystem + imagens Docker)
  * OWASP Dependency-Check
  * SBOM CycloneDX (Syft)
* **DefectDojo (Open Source)**: agregação e visualização de findings
* **Cloudflare Tunnel**: exposição temporária do DefectDojo local para o pipeline

---

## 3. Instalação e Execução do DefectDojo (Local)

### 3.1 Clonar o projeto

```bash
git clone https://github.com/DefectDojo/django-DefectDojo.git
cd django-DefectDojo
```

### 3.2 Iniciar com Docker Compose

```bash
docker compose up -d
```

Serviços iniciados:

* Nginx (porta 8080)
* Django (uwsgi)
* PostgreSQL
* Redis/Valkey

Acesso local:

```
http://localhost:8080
```

---

## 4. Criar Superuser no DefectDojo

```bash
docker compose exec uwsgi python manage.py createsuperuser
```

Depois do login:

* Criar **Product**
* Criar **Engagement**
* Guardar o **Engagement ID**

---

## 5. Criar API Token

No UI do DefectDojo:

* User menu → API v2 Tokens
* Criar token
* Guardar com segurança (usado no pipeline)

---

## 6. Expor o DefectDojo com Cloudflare Tunnel

### 6.1 Instalar cloudflared

```bash
brew install cloudflare/cloudflare/cloudflared
```

### 6.2 Criar tunnel temporário

```bash
cloudflared tunnel --url http://localhost:8080
```

Exemplo de URL gerada:

```
https://xxxx.trycloudflare.com
```

Esta URL é usada pelo GitHub Actions para comunicar com o DefectDojo local.

---

## 7. Configuração de Secrets no GitHub

Em **Settings → Secrets and variables → Actions**:

| Secret                   | Descrição                                                                         |
| ------------------------ | --------------------------------------------------------------------------------- |
| DEFECTDOJO_URL           | URL Cloudflare ([https://xxxx.trycloudflare.com](https://xxxx.trycloudflare.com)) |
| DEFECTDOJO_API_KEY       | API Token do DefectDojo                                                           |
| DEFECTDOJO_ENGAGEMENT_ID | ID do Engagement                                                                  |

---

## 8. Pipeline CI/CD (GitHub Actions)

O workflow executa:

1. Checkout do código
2. Trivy filesystem scan (dependências)
3. Build das imagens Docker (backend + frontend)
4. Trivy image scan
5. OWASP Dependency-Check
6. Geração de SBOM (CycloneDX)
7. Upload de artefactos
8. Upload automático para o DefectDojo

---

## 9. Script de Upload para o DefectDojo

O upload é feito via **API v2** (`/api/v2/import-scan/`) usando `requests`.

### scan_type corretos (Open Source)

| Ferramenta       | scan_type             |
| ---------------- | --------------------- |
| Trivy            | Trivy Scan            |
| Dependency-Check | Dependency Check Scan |
| SBOM CycloneDX   | CycloneDX Scan        |

O script define também `test_title` para separar resultados dentro do mesmo Engagement.

---

## 10. Resultados Obtidos

* ✔ Vulnerabilidades Trivy importadas com sucesso
* ✔ Backend e Frontend separados por Test
* ✔ SBOM importado como inventário de componentes
* ✔ Centralização completa no DefectDojo
* ✔ Pipeline totalmente automatizado

Notas:

* SBOM não gera findings por defeito (apenas inventário)
* Dependency-Check requer output XML para compatibilidade total

---

## 11. Boas Práticas DevSecOps Demonstradas

* Security as Code
* Shift-left security
* Centralização de vulnerabilidades
* Automatização completa
* Uso exclusivo de ferramentas open-source

---

## 12. Diagrama de Funcionamento

```
┌──────────────┐
│   Developer  │
└──────┬───────┘
       │ push / PR
       ▼
┌────────────────────┐
│   GitHub Actions   │
│  (CI/CD Pipeline)  │
└──────┬─────────────┘
       │
       │ SCA Tools
       │
       ├─ Trivy (FS + Images)
       ├─ Dependency-Check
       └─ SBOM (CycloneDX)
       │
       ▼
┌────────────────────┐
│  JSON / XML / SBOM │
│     Artefacts      │
└──────┬─────────────┘
       │
       │ API v2 (/import-scan)
       ▼
┌────────────────────────────┐
│        DefectDojo          │
│  (Local via Docker)        │
└──────┬─────────────────────┘
       │
       │ Cloudflare Tunnel
       ▼
┌────────────────────────────┐
│  https://*.trycloudflare   │
│    (Secure Exposure)       │
└────────────────────────────┘
```

---

## 13. Conclusão

Este projeto demonstra com sucesso a integração de análises de segurança de dependências num pipeline CI/CD moderno, com gestão centralizada de vulnerabilidades no DefectDojo. A solução é escalável, automatizada, alinhada com práticas DevSecOps e adequada a ambientes académicos e reais.
