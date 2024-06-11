# Explanation

## Server Side
`./config2.ipynb` 를 실행하여 `model.fuse`를 실행하여 YOLO 모델을 다운받는다.
이후 `server.py`를 실행하여 준비 상태에 대기시킨다.

## Client Side
`client.py`를 실행한다

## Transaction
#### CLIENT $\bm\rarr$ SERVER
``` python
{
    "start":int[2]
    "end":int[2] 
    "color":str
    "video":str
}[]
```

#### SERVER $\bm\rarr$ CLIENT
```python
{
    'person': float[]
    'bicycle': float[]
    'motorcycle': float[]
    'car': float[]
    'bus': float[]
    'truck': float[]
    'color': str    
}[]
```
in case of error
```python
{
    'error': str
}
```