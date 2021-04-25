echo off
call activate tf-gpu
python ./interface.py
call conda deactivate
