MnS

│

├── app

│   │

│   ├── main.py                 # FastAPI App 생성

│   ├── dependencies.py         # Dependency Injection

│   │

│   ├── api

│   │    ├── health.py

│   │    ├── regression.py

│   │    ├── estimation.py

│   │    ├── simulation.py

│   │    └── router.py

│   │

│   ├── schemas

│   │    ├── regression.py

│   │    ├── estimation.py

│   │    ├── simulation.py

│   │    └── common.py

│   │

│   ├── services

│   │    ├── regression\_service.py

│   │    ├── estimation\_service.py

│   │    ├── simulation\_service.py

│   │    └── report\_service.py

│   │

│   ├── models

│   │    │

│   │    ├── ecm

│   │    │    ├── thevenin\_1rc.py

│   │    │    ├── thevenin\_2rc.py

│   │    │    ├── randles.py

│   │    │    └── ocv\_model.py

│   │    │

│   │    └── regression

│   │         ├── linear.py

│   │         ├── nonlinear.py

│   │         ├── optimizer.py

│   │         └── statistics.py

│   │

│   ├── data

│   │    ├── loader.py

│   │    ├── preprocessing.py

│   │    ├── validator.py

│   │    ├── exporter.py

│   │    ├── input

│   │    ├── output

│   │    └── temp

│   │

│   ├── utils

│   │    ├── file\_utils.py

│   │    ├── math\_utils.py

│   │    ├── plot\_utils.py

│   │    └── logger.py

│   │

│   ├── core

│   │    ├── config.py

│   │    ├── constants.py

│   │    ├── paths.py

│   │    ├── exceptions.py

│   │    └── settings.py

│   │

│   ├── static

│   │    ├── css

│   │    ├── js

│   │    └── image

│   │

│   └── templates

│        ├── index.html

│        ├── upload.html

│        └── result.html

│

├── sample\_data

│   ├── csv

│   │    ├── HPPC.csv

│   │    ├── Pulse.csv

│   │    └── OCV.csv

│   │

│   └── result

│        ├── Regression\_Result.csv

│        └── Simulation\_Result.csv

│

├── tests

│   ├── test\_regression.py

│   ├── test\_estimation.py

│   ├── test\_simulation.py

│   └── test\_api.py

│

├── docs

│   ├── ProjectTree.md

│   ├── API.md

│   ├── UserGuide.md

│   ├── DeveloperGuide.md

│   └── Workflow.md

│

├── scripts

│   ├── build.ps1

│   ├── clean.ps1

│   ├── run\_server.ps1

│   └── package.ps1

│

├── config

│   ├── app.json

│   └── logging.yaml

│

├── logs

│   └── app.log

│

├── resources

│   ├── icon.ico

│   └── logo.png

│

├── requirements.txt

├── requirements-dev.txt

├── run.py

├── mns\_app.spec

├── Dockerfile

├── README.md

└── .gitignore



\# recommended file structure for MnS pjt (ChatGPT -> Claude)

MnS/

├── .venv/                          	(\*) % 가상환경 (필수, 개발 자체가 안 됨)

├── .vscode/

│   ├── settings.json            	( ) % 없어도 개발 가능 (interpreter만 잘 잡히면)

│   └── launch.json              	( ) % 디버깅 편의용, MVP 필수는 아님

├── app/                             	(\*) % 패키지 루트

│   ├── \_\_init\_\_.py                  	(\*) % 없으면 app이 패키지로 안 잡힘

│   ├── main.py                      	(\*) % FastAPI 진입점 (핵심)

│   ├── api/                         	(\*)

│   │   ├── \_\_init\_\_.py              	(\*)

│   │   └── routes\_simulation.py 	(\*) % 라우터 (엔드포인트 없으면 앱 자체가 없음)

│   ├── core/

│   │   ├── \_\_init\_\_.py              	(\*) % core 폴더 쓸 거면 필요

│   │   ├── config.py                (\*) % pyinstaller 경로처리 때문에 사실상 필수

│   │   └── security.py              (\*) % MVP에서 생략 (인증 없음)

│   ├── models/

│   │   ├── \_\_init\_\_.py

│   │   └── schemas.py             ( ) % MVP는 dict로 대체 가능, 생략 OK

│   ├── services/                    	(\*)

│   │   ├── \_\_init\_\_.py              	(\*)

│   │   └── simulation.py      	(\*) % 핵심 로직, 절대 생략 불가

│   ├── data/                          ( ) % 샘플 데이터 넣을 거면만 필요

│   ├── static/                      	(\*) % 프론트 파일 (index.html, js, css)

│   └── templates/                   ( ) % Jinja2 SSR 안 쓰면 생략

├── tests/                               	( ) % MVP 단계면 생략, 이후 필수

│   ├── test\_api.py

│   └── test\_services.py

├── run.py                           	(\*) % pyinstaller entry point (main.py와 역할 분리시 필요)

├── .env                                 	( ) % 환경변수 쓸 게 있으면

├── .env.example                       ( ) % .env 쓸 때만 의미 있음

├── .gitignore                       	(\*) % git 쓴다면 사실상 필수 (venv/캐시 커밋 방지)

├── requirements.txt                 	(\*) % 배포/재현성 위해 필수

└── README.md                       ( ) % 없어도 동작엔 지장 없음



