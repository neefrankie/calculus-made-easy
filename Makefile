watch:
	fswatch -o templates | xargs -n1 -I{} make compile
compile:
	. myenv/bin/activate && python3 compile_templates.py
deploy: 
	rsync --exclude .git -avz public nadvornix_calculusmadeeasy@ssh.nyc1.nearlyfreespeech.net:/home/public

test:
	linkchecker http://localhost/cme/; 	linkchecker http://calculusmadeeasy.org/

