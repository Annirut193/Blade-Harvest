import cv2
import mediapipe as mp
import pygame
import random
import multiprocessing

# Hand Tracking Function
def hand_tracking(queue):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                index_finger_tip = hand_landmarks.landmark[8]
                finger_x = int(index_finger_tip.x * 1920)  # Adjusted for full screen
                finger_y = int(index_finger_tip.y * 1080)
                queue.put((finger_x, finger_y))

        cv2.waitKey(10)

    cap.release()
    hands.close()
    cv2.destroyAllWindows()

# Game Function
def game_main(queue):
    pygame.init()
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Hand-Controlled Fruit Ninja")

    # Load and Scale Background Image
    background = pygame.image.load("resized_background.png")
  
    # Load and Scale Fruit Images
    fruit_images = [
        pygame.image.load("cherry-removebg-preview.png"),
        pygame.image.load("fruits-removebg-preview.png"),
        pygame.image.load("watermelon-removebg-preview.png"),
        pygame.image.load("strwberry-removebg-preview.png"),
    ]
    fruit_size = 150
    fruit_images = [pygame.transform.scale(img, (fruit_size, fruit_size)) for img in fruit_images]

    # Colors & Variables
    BLACK = (0, 0, 0)
    BOMB_COLOR = (255, 0, 0)  # Bomb color red
    BOMB_SIZE = 50
    FPS = 60
    clock = pygame.time.Clock()

    # Game Stats
    score = 0
    missed_fruits = 0
    max_missed_fruits = 10
    objects = []
    running = True
    hand_x, hand_y = WIDTH // 2, HEIGHT // 2

    # Function to Spawn Objects (Fruits & Bombs)
    def spawn_object():
        if random.random() < 0.7:  # 70% chance of fruit
            fruit = {
                "type": "fruit",
                "x": random.randint(50, WIDTH - 150),
                "y": HEIGHT,
                "prev_x": None,
                "prev_y": None,
                "image": random.choice(fruit_images),
                "speed": random.randint(4, 7),
                "sliced": False,
            }
            objects.append(fruit)
        else:  # 30% chance of bomb
            bomb = {
                "type": "bomb",
                "x": random.randint(50, WIDTH - BOMB_SIZE),
                "y": HEIGHT,
                "prev_x": None,
                "prev_y": None,
                "size": BOMB_SIZE,
                "speed": random.randint(4, 7),
                "sliced": False,
            }
            objects.append(bomb)

    # Game Loop
    while running:
        screen.blit(background, (0, 0))  # Draw background first

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Get Hand Position from Queue
        if not queue.empty():
            hand_x, hand_y = queue.get()

        # Spawn Objects
        if random.random() < 0.02 and len(objects) < 15:
            spawn_object()

        # Move & Draw Objects
        for obj in objects[:]:  # Copy list to avoid modification errors
            obj["y"] -= obj["speed"]

            # Remove objects if they go off screen
            if obj["y"] < -50:
                if obj["type"] == "fruit" and not obj["sliced"]:
                    missed_fruits += 1
                objects.remove(obj)
                continue  # Skip drawing removed objects

            # Draw objects
            if obj["type"] == "fruit" and not obj["sliced"]:
                screen.blit(obj["image"], (obj["x"], obj["y"]))
            elif obj["type"] == "bomb" and not obj["sliced"]:
                pygame.draw.rect(screen, BOMB_COLOR, (obj["x"], obj["y"], obj["size"], obj["size"]))

            # Store previous position before movement
            if obj["prev_x"] is None:
                obj["prev_x"], obj["prev_y"] = obj["x"], obj["y"]

            # Check for slicing using bounding box method
            if obj["type"] == "fruit":
                if obj["x"] <= hand_x <= obj["x"] + fruit_size and obj["y"] <= hand_y <= obj["y"] + fruit_size:
                    obj["sliced"] = True
                    score += 1
                    objects.remove(obj)

            elif obj["type"] == "bomb":
                if obj["x"] <= hand_x <= obj["x"] + obj["size"] and obj["y"] <= hand_y <= obj["y"] + obj["size"]:
                    obj["sliced"] = True
                    running = False  # End game if bomb is sliced

            # Update previous position after movement
            obj["prev_x"], obj["prev_y"] = obj["x"], obj["y"]

        # Display Score & Missed Fruits
        font = pygame.font.Font(None, 50)
        score_text = font.render(f"Score: {score}", True, BLACK)
        missed_text = font.render(f"Missed: {missed_fruits}/{max_missed_fruits}", True, BLACK)
        screen.blit(score_text, (20, 20))
        screen.blit(missed_text, (20, 70))

        # Draw Hand Cursor
        pygame.draw.circle(screen, (255, 0, 0), (hand_x, hand_y), 10)

        # Update Screen
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# Main Execution
if __name__ == "__main__":
    queue = multiprocessing.Queue()
    hand_process = multiprocessing.Process(target=hand_tracking, args=(queue,))
    hand_process.start()
    game_main(queue)
    hand_process.terminate()
