# park.ingyeom OTT Churn Prediction Workspace

> 프로젝트 개요

이 폴더는 OTT 구독자의 재결제 여부와 이탈 가능성을 분석하기 위한 개인 작업 공간입니다. 처음에는 개인 폴더 안에서 EDA, 전처리, 파생변수 생성, 모델링 실험이 따로 진행되었고, 이후 Git 저장소로 옮겨지면서 경로와 파일 위치가 섞였습니다.

이번 정리는 기존 작업물을 삭제하는 방식이 아니라, 분석 흐름이 보이도록 다시 배치하는 방식으로 진행했습니다. 면접관이나 팀원이 이 폴더를 처음 보더라도, 데이터가 어떤 단계를 거쳐 모델링까지 이어졌는지 이해할 수 있게 만드는 것이 목표입니다.

> 현재까지 진행된 단계

이 프로젝트는 단순히 시작 단계에 머물러 있지 않습니다. 기존 파일을 기준으로 보면 다음 단계까지 진행된 상태입니다.

1. 원천 데이터 확인
2. Membership, View History, User Mapping 중심의 기초 EDA
3. user_id와 user_no 매핑 작업
4. 연령 이상치와 미인증 유저 문제 검토
5. 시청 이력 기반 파생변수 생성
6. 모델 입력용 데이터셋 생성
7. 다중공선성 확인
8. Logistic Regression, Random Forest, XGBoost, CatBoost, LightGBM, GradientBoosting 모델 비교
9. 일부 모델에 대한 Optuna 튜닝 실험

즉, 현재 상태는 "분석을 시작해야 하는 단계"가 아니라, "여러 실험을 재현 가능한 순서로 정리해야 하는 단계"에 가깝습니다.

> 폴더 구조

```text
park.ingyeom/
│
├─ _data/
│  ├─ 01_raw/
│  ├─ 02_interim/
│  └─ 03_processed/
│
├─ notebooks/
│  ├─ 01_data_check/
│  ├─ 02_preprocessing/
│  ├─ 03_eda/
│  ├─ 04_feature_engineering/
│  ├─ 05_modeling/
│  └─ 06_tuning/
│
├─ src/
│  ├─ config.py
│  ├─ scraping/
│  └─ reporting/
│
├─ models/
├─ reports/
└─ archive/
```

> 데이터 폴더 기준

`_data/01_raw`는 원본 또는 원본에 가까운 데이터가 들어가는 곳입니다. 이 폴더의 파일은 가능하면 수정하지 않습니다. 원본을 직접 고치면 이후 분석에서 무엇이 바뀌었는지 추적하기 어렵기 때문입니다.

`_data/02_interim`은 중간 가공 데이터가 들어가는 곳입니다. 예를 들어 user mapping을 붙였거나, 영화 크롤링 결과를 임시로 저장했거나, 최종 모델 입력으로 확정되기 전의 병합 데이터가 여기에 해당합니다.

`_data/03_processed`는 모델링이나 최종 분석에 사용할 수 있는 정리된 데이터가 들어가는 곳입니다. 현재 핵심 후보 파일은 `final_merged_user(단칼)_v3.xlsx`와 `Membership_v3.xlsx`입니다.

> 노트북 폴더 기준

`notebooks/01_data_check`는 원천 데이터를 처음 확인하는 단계입니다.

`notebooks/02_preprocessing`은 데이터 병합, user mapping, 이상치 처리처럼 모델링 이전에 데이터를 정리하는 단계입니다.

`notebooks/03_eda`는 변수 분포, 인증 여부, 연령, 결제 방식, 시청 이력 등을 탐색하는 단계입니다.

`notebooks/04_feature_engineering`은 모델에 넣을 파생변수를 만들고, 다중공선성처럼 변수 간 관계를 점검하는 단계입니다.

`notebooks/05_modeling`은 기본 모델을 비교하는 단계입니다. 이 단계에서는 모델의 성능을 빠르게 비교하고, 어느 모델군이 가능성이 있는지 확인합니다.

`notebooks/06_tuning`은 Optuna와 같은 튜닝 실험을 포함한 고도화 단계입니다. 현재 `membership_v2.ipynb`, `membership_v3.ipynb`가 이 단계에 배치되어 있습니다.

> src 폴더 기준

`src/config.py`는 프로젝트 경로를 한 곳에서 관리하기 위한 파일입니다. 개인 폴더에서 Git 저장소 구조로 바뀌면서 상대 경로가 많이 깨졌기 때문에, 앞으로는 노트북마다 직접 경로를 쓰기보다 이 파일을 기준으로 경로를 통일하는 것이 좋습니다.

예를 들어 모델 입력 데이터 경로는 다음처럼 관리합니다.

```python
from src.config import FINAL_MERGED_USER_V3_PATH

print(FINAL_MERGED_USER_V3_PATH)
```

`src/scraping`에는 외부 영화 데이터를 수집하는 스크립트가 들어 있습니다.

`src/reporting`에는 분석 결과를 리포트 형태로 만드는 스크립트가 들어 있습니다.

> archive 폴더 기준

`archive`는 당장 최종 흐름에는 포함하지 않지만, 삭제하기에는 아까운 작업물을 보관하는 곳입니다.

`archive/legacy_crawling`은 이전 크롤링 실험입니다.

`archive/learning_notes`는 프로젝트 직접 산출물이라기보다 학습용 노트북에 가깝습니다.

`archive/old_experiments`는 현재 최종 흐름에서 제외한 과거 실험입니다.

> 주의할 점

이번 정리는 파일과 폴더 구조를 재배치한 작업입니다. 기존 노트북 내부의 `../Dataset/Membership.xlsx`, `final_merged_user(단칼)_v3.xlsx` 같은 상대 경로는 아직 모두 수정된 상태가 아닐 수 있습니다.

따라서 다음 단계는 노트북을 하나씩 열어, 데이터 경로를 `src/config.py` 기준으로 바꾸는 것입니다. 이 작업을 마치면 폴더 구조뿐 아니라 실행 흐름까지 재현 가능한 형태에 가까워집니다.

> 추천 실행 순서

처음 이 프로젝트를 다시 실행한다면 다음 순서로 보는 것이 가장 자연스럽습니다.

1. `notebooks/01_data_check`
2. `notebooks/02_preprocessing`
3. `notebooks/03_eda`
4. `notebooks/04_feature_engineering`
5. `notebooks/05_modeling`
6. `notebooks/06_tuning`

이 순서는 데이터가 원본에서 출발해, 정제되고, 탐색되고, 파생변수로 확장된 뒤, 모델링과 튜닝으로 이어지는 흐름입니다.

> 정리 의도

이 구조의 핵심은 기교가 아니라 설명 가능성입니다. 폴더 이름만 보고도 "이 프로젝트는 데이터를 받고, 전처리하고, 탐색하고, 파생변수를 만들고, 모델을 비교한 뒤, 튜닝까지 진행했구나"라고 이해할 수 있어야 합니다.

분석 프로젝트에서 좋은 구조는 복잡한 구조가 아니라, 나중에 다시 열었을 때도 스스로에게 설명되는 구조입니다. 이 폴더는 그 기준에 맞춰 정리했습니다.
