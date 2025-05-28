This is an example "standalone" app. Compare its structure and operation to the existing user_example driven "hello_robot" project in this repo. In the case of a standalone app, you do not need to move the code anywhere, just run it from the entrypoint as described below.

Importantly, note the parity between the sim construct described in `examples/hello_robot_standalone/simulation/jetbot_sim.py` and the actor construct described in `examples/hello_robot_standalone/actors/jetbot.py`. At this level of example, a 1:1 relationship between a sim definition and an actor definition is important to understand.

They are instantiated in simulation.py. 


to start:
navigate to `examples/hello_robot_standalone/actors` and run `para docker deploy node`

the other actors will be prepared when we start the demo.

navigate to `examples/hello_robot_standalone` and run `...<isaac path>/python.sh isaac_app.py`

You'll see the actors initialized in the terminal, but can also see them via the docker extension. 

Go to `http://localhost:3023/` advanced, and test the skills. 