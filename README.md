# 🗂️ Media Cleaner

Ferramenta de linha de comando para deduplicação de arquivos em sistemas de arquivos locais. Escaneia um diretório recursivamente, calcula hashes criptográficos de cada arquivo e move automaticamente as cópias duplicadas para uma pasta de quarentena sem deletar nada permanentemente.

---
 
## 📌 Funcionalidades

- Scan recursivo de diretórios com exclusão automática de pastas ocultas e de quarentena
- Hashing com BLAKE3 para garantir eficiência e segurança ao trabalhar com um grande volume de dados
- Hashing paralelo via `ThreadPoolExecutor` para maximizar throughput em I/O
- Persistência em SQLite com upsert idempotente, re-execuções são seguras
- Deduplicação por hash exato: mantém o arquivo mais antigo, move as cópias
- Movimentação para pasta `to_delete` na raiz do drive, nenhum arquivo é deletado permanentemente
- Limpeza automática de diretórios vazios após movimentação
- Log estruturado com rastreamento completo das movimentações

---

## 🏗️ Arquitetura

O projeto segue uma arquitetura em camadas inspirada no padrão MVC + Repository, com a seguinte separação de responsabilidades:

```
Controller  →  FileService  →  FileScanner
                            →  FileHasher
                            →  FileRepository
                            →  CleaningService
```

---

## 🗄️ Schema do Banco de Dados

```sql
CREATE TABLE files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    NOT NULL UNIQUE,
    name        TEXT    NOT NULL,
    extension   TEXT,
    size        INTEGER NOT NULL,
    hash        TEXT,
    created_at  TEXT
);

CREATE INDEX idx_files_hash ON files(hash);
CREATE INDEX idx_files_size ON files(size);
```

A detecção de duplicatas é feita via self-join com `GROUP BY hash HAVING COUNT(*) > 1`, retornando apenas hashes com mais de uma ocorrência.

---

## 🚀 Como usar

### Pré-requisitos

```bash
pip install blake3
```

### Executar

```bash
python -m src.main "C:\directory"
```

### Exemplo de saída

```
2025-01-17 14:32:01 [INFO] Iniciando scan em: C:\directory
2025-01-17 14:32:04 [INFO] [SUCCESS]
2025-01-17 14:32:04 [INFO] Diretório:              C:\directory
2025-01-17 14:32:04 [INFO] Arquivos encontrados:   1.432
2025-01-17 14:32:04 [INFO] Grupos de duplicatas:   15
2025-01-17 14:32:04 [INFO] Arquivos movidos:       15

2025-01-17 14:32:04 [INFO] --- Arquivos movidos ---
2025-01-17 14:32:04 [INFO]
  Duplicata:    C:\directory\fotos\copia.jpg
  Movido para:  C:\to_delete\directory\fotos\copia.jpg
  Original:     C:\directory\fotos\foto.jpg
```

---

## 📁 Estrutura do Projeto

```
media_cleaner/
├── media_cleaner.db
├── media_cleaner.log
└── src/
    ├── main.py
    ├── controllers/
    │   └── file_controller.py
    ├── core/
    │   ├── hasher.py
    │   └── scanner.py
    ├── database/
    │   └── connection.py
    ├── models/
    │   └── file_model.py
    ├── repositories/
    │   └── file_repository.py
    ├── services/
    │   ├── cleaning_service.py
    │   └── file_service.py
    └── utils/
        └── logger.py
```

---

## 🛠️ Tech Stack

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | Linguagem principal |
| BLAKE3 | Hashing criptográfico de arquivos |
| SQLite | Persistência local |
| ThreadPoolExecutor | Paralelismo no hashing |
| argparse | Interface de linha de comando |
| logging | Log estruturado em arquivo e terminal |
