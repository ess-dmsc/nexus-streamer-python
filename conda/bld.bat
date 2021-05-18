Rem pip install into the site-packages directory
python -m pip install --target=%PREFIX\Lib\site-packages --ignore-installed --no-deps -vv .

Rem Move the entry point script into bin
mkdir %PREFIX\bin
move  %PREFIX\Lib\site-packages\bin\nexus_streamer %PREFIX\bin\nexus_streamer
