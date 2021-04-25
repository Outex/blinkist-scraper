echo off
call activate tf-gpu
SET /A num=%RANDOM% * 20 / 32768 + 5
echo %num%
python blinkistscraper Magana1111@web.de Magana1111 --language en --daily-book --audio --concat-audio --cooldown %num% --create-html --create-epub --save-cover --embed-cover-art
SET /A num=%RANDOM% * 20 / 32768 + 5
echo %num%
python blinkistscraper Magana1111@web.de Magana1111 --language de --daily-book --audio --concat-audio --cooldown %num% --create-html --create-epub --save-cover --embed-cover-art
call conda deactivate
