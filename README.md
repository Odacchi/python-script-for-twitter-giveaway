## 実行に必要なツール

Pyenv + Poetry

## 準備

pyenvでpython3.10.4をインストールする。
```
pyenv install 3.10.4
```

```
poetry install
```

## 実行

### 設定ファイル

.env.distをコピーして.envを作成
```
cp .env.dist .env
```

### 起動

```
poetry shell
cd src
python main.py
```

もしくは

```
cd src
poetry run python main.py 
```