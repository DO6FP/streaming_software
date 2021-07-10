# start broadway daemon
broadwayd :4& 

# run main program
GDK_BACKEND=broadway BROADWAY_DISPLAY=:4  ./main.py

# open http://nuc2:8085/ in browser
