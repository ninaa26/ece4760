SIMPLE = {'3.1': "The demo had two balls. We only need one, so we throw away the second ball's notes: where it is and how fast it's moving.",
 '3.2': "The semaphore was like a walkie-talkie between the Pico's two brains (its two cores). We're only using one brain now, so nobody is on the other end.",
 '3.3': "This part listened for typing from the laptop. We won't type anything, so it goes.",
 '3.4': "This was the second brain's to-do list for the second ball. No second ball, no list.",
 '3.5': "This line pressed the walkie-talkie button. The walkie-talkie is gone, so this line has to go too, or the code won't compile.",
 '3.6': 'These lines woke up the second brain. We let it sleep for now; week 3 wakes it up again.',
 '3.7': 'We stop asking the Pico to run the typing-listener we just deleted.',
 '3.8': "We add a name for the number 16 667. It's how many millionths of a second each picture gets, like a time limit per test question. We also name the pin the little light on the Pico is "
        'connected to.',
 '3.9': 'Two more boxes for notes: when this picture started, and how much time was left last time.',
 '3.10': 'Start the stopwatch at the beginning of every picture.',
 '3.11': 'Write "Spare time" under the count. Then check the stopwatch: if we used more than our time limit, switch on the little light, like a warning light on a car dashboard.',
 '3.12': "Tell the Pico that the light's pin is something it controls (an output), not something it listens to.",
 '2.1': 'We give the knob\'s two wires names (GP2 and GP3), a box for the number on the screen, a note of where the knob is right now, and a cheat sheet. The cheat sheet answers: "the switches were '
        'like this, now they\'re like that: did the knob move forward or backward?"',
 '2.2': 'This is a doorbell that rings every time either switch in the knob flips. It checks the cheat sheet and keeps a running tally. When the knob settles into its next click, the number on '
        'screen changes by one. If a switch rattles, the tally goes forward one and back one, so it cancels out by itself.',
 '2.3': 'Tell the Pico that A and B are inputs with pull-ups, note where the knob starts, then install the doorbell on both switches. This runs once, when the Pico starts.',
 '2.4': "A box to write the words in before drawing them. <code>static</code> means it keeps what's inside even when the program takes a break.",
 '2.5': 'Every picture, write "Encoder Count: " and the number in the top-left corner.',
 '4.1': 'We add brackets so the shortcut always works on the whole thing you give it, just like writing (2 + 3) × 4 when you mean it, instead of 2 + 3 × 4.',
 '4.2': "Take away the box's walls and put in the handout's numbers: how strong gravity is, how big the ball is, how big the screen is.",
 '4.3': 'We make a "ball card" that holds everything about one ball: where it is and how fast it\'s going.',
 '4.4': 'Two instructions. "Start a ball": put it at the top middle, not falling yet, with a tiny random push sideways. "Move a ball one step": move it, start over if it fell off the bottom, bounce '
        'if it hit a side, then make it a bit faster because of gravity.',
 '4.5': 'Before the animation begins, put the first ball at the top.',
 '4.6': 'For every picture: move the ball one step, then draw it as a small blue circle.',
 '4.7': "Shuffle the random numbers, like shuffling a deck of cards, so the sideways push isn't the same every time.",
 '5.1': 'More numbers from the handout: how big the peg is, how bouncy things are, and how close counts as touching (10 pixels, centre to centre).',
 '5.2': "The ball remembers the last peg it bumped, so a long touch doesn't count as lots of bumps.",
 '5.3': 'A list of where the pegs are. Right now the list has just one peg.',
 '5.4': "A brand-new ball hasn't bumped anything yet.",
 '5.5': "A fast way to guess a distance without the slow square-root button. It's almost right (within 4 %), like estimating instead of getting out a ruler.",
 '5.6': "Is the ball touching the peg? If so: find the direction that points straight away from the peg. Turn the ball's movement around in that direction, like a ball bouncing off a wall. Move the "
        "ball so it isn't stuck inside the peg. And if it's a new peg, slow it down by half.",
 '5.7': 'Draw the peg as a white dot.',
 '5.8': 'Put the peg right under where balls are dropped, so the ball lands on it.',
 '6.1': 'Tell the build tool to include the code that talks to the sound chip (the DAC).',
 '6.2': 'Tell the compiler the names of that code, so it recognises them.',
 '6.3': 'Settings for the sound (which wires, how fast to play it, how long it is) and an empty list to hold it.',
 '6.4': 'First, make the sound once: a list of 1 323 numbers that trace a "thunk" wave. Then set up two helper robots (DMA channels). One carries the numbers to the sound chip, one at a time; the '
        'other rewinds the list back to the start. Last, a one-line "play" button.',
 '6.5': 'Press play when the ball hits a new peg.',
 '6.6': "Set up the sound when the Pico starts. Do it after the screen is set up, so they don't grab the same helper robots."}

BIG = {'w1-s0': "You're setting up your workbench. It's like getting all the ingredients and tools out before you start cooking, so you don't have to stop halfway.",
 'w1-s1': "Before you change a recipe, make it once exactly as written. If the demo's balls show up, your wires are right. Then, if something breaks later, you know it's your change and not the "
          'wiring.',
 'w1-s2': "The knob has two tiny switches inside. Turning it flips them in a certain order. If you know which one flipped first, you know which way it turned. It's like knowing which way someone "
          'walked through a hallway with two doors by which door opened first.',
 'w1-s3': "We clean out things we don't need, like clearing a messy desk before homework. Then we add a stopwatch that shows how much time is left for each picture, like the clock during a test.",
 'w1-s4': "Each picture, the ball moves a little, then gravity makes it a little faster. It's like a ball rolling down a hill: it keeps speeding up.",
 'w1-s5': 'When the ball hits the peg, it bounces away, like a pool ball bouncing off another one. Then it loses half its speed, like a basketball that bounces a bit lower each time.',
 'w1-s6': 'A sound is just a list of numbers, like the pages of a flipbook, but for your ears. DMA is a helper robot that flips the pages for you, so the Pico can keep moving the ball.'}

CONCEPT = {'<h4>How it works: VGA</h4>': 'A monitor draws its picture one row of dots at a time, super fast: 60 whole pictures every second. The Pico sends it two timing signals ("start a new row!" and "start '
                               'a new picture!") and three colour signals. <b>Double buffering</b> is like having two whiteboards: you draw on one while everyone looks at the other, then you swap '
                               'them. Nobody ever sees a half-finished drawing.',
 "<h4>How it works: a tour of the demo's <code>animation.c</code></h4>": 'Before you change something, look around it once, like reading a map before a trip. <b>Protothreads</b> are how the Pico '
                                                                         'takes turns between jobs: each job does a bit, then says "your turn" and waits.',
 '<h4>Before the code: how an encoder works</h4>': '<b>Pull-up:</b> a switch that isn\'t pressed is connected to nothing, so the Pico can\'t tell what it is. A pull-up gently holds the wire at "1", '
                                                   'like a spring holding a door shut, until the switch pulls it down to "0". <b>Interrupt:</b> a doorbell. You don\'t keep opening the door to check; '
                                                   "the bell tells you when someone's there. <b>Bounce:</b> when metal switches touch they rattle for a moment, like a door that shakes before it "
                                                   'settles. The code follows every rattle, and they cancel out.',
 '<h4>Before the code: three ideas</h4>': '<b>y goes down:</b> the screen counts from the top, like reading a page, so falling means y gets bigger. <b>Fixed point:</b> the Pico is fastest with whole '
                                          'numbers, so we do what shops do with money: count in cents instead of dollars. $0.37 becomes 37 cents, with no decimal point needed. Here each 1 is split '
                                          'into 32 768 tiny pieces instead of 100.',
 '<h4>Before the code: the bounce in five ideas</h4>': 'Picture throwing a ball at a wall at an angle. The part of its motion going <i>into</i> the wall flips around. The part going <i>along</i> the '
                                                       'wall stays the same. A peg is a round wall, so "into the wall" means "toward the peg\'s centre". The maths below just works out which way that '
                                                       'is.',
 '<h4>Before the code: a sound is a list of numbers, and DMA sends it</h4>': 'A speaker moves back and forth to make sound. Each number in the list says how far to push it. Play 44 105 numbers a '
                                                                             'second and your ear hears a smooth sound, like flipbook pages turning into a movie. <b>DMA</b> is a conveyor belt: the '
                                                                             'Pico switches it on once, and the belt delivers every number by itself.',
 '<h4>How the hardware is set up</h4>': 'Every part talks to the Pico through wires on its pins. Each pin has two numbers, like a house with a street number and a family name: the <b>physical '
                                        'number</b> (its position on the board, 1 to 40) and the <b>GPIO name</b> the code uses (like GP16). The diagram shows both so you can find the right hole. '
                                        '<b>GND</b> (ground) is the shared "zero volts" every part needs to agree on, like everyone measuring height from the same floor.',
 '<h4>Make your copy of the demo</h4>': "You're photocopying the teacher's worksheet so you can write on your copy and keep the original clean.",
 '<h4>The build-and-flash routine</h4>': '<b>Building</b> turns your C code (words people can read) into a program the Pico can run (numbers). <b>Flashing</b> copies that program onto the Pico, like '
                                         'saving a file onto a USB stick. Double-pressing reset puts the Pico in "ready to receive" mode.',
 '<h4>Wire the VGA connector</h4>': "The VGA plug has separate wires for red, green and blue light, plus two timing wires. The resistors make the Pico's signal gentle enough for the monitor, like "
                                    'turning a tap down to a trickle.',
 '<h4>How it works</h4>': "Your monitor shows 60 pictures a second, so the Pico gets about 1/60 of a second (16 667 millionths) to make each one. <b>Spare time</b> is how much of that it didn't "
                          'need, like finishing a test with 10 minutes left. More balls later means less spare time. If it ever runs out, the little light turns on.',
 '<h4>Know the part</h4>': 'Not every knob is the same. Some click once per full turn of the switch pattern, some click twice. The code number printed on the side tells you which, like a shoe size.'}
