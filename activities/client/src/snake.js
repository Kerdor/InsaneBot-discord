const GRID_SIZE = 20;
const TICK_MS = 120;

const DIRECTIONS = {
    ArrowUp: { x: 0, y: -1 },
    ArrowDown: { x: 0, y: 1 },
    ArrowLeft: { x: -1, y: 0 },
    ArrowRight: { x: 1, y: 0 },
};

export class SnakeGame {
    constructor(canvas, scoreElement, statusElement) {
        this.canvas = canvas;
        this.context = canvas.getContext("2d");
        this.scoreElement = scoreElement;
        this.statusElement = statusElement;
        this.cellSize = canvas.width / GRID_SIZE;
        this.timer = null;
        this.reset();
    }

    reset() {
        this.snake = [
            { x: 10, y: 10 },
            { x: 9, y: 10 },
            { x: 8, y: 10 },
        ];
        this.direction = { x: 1, y: 0 };
        this.nextDirection = { x: 1, y: 0 };
        this.score = 0;
        this.food = this.createFood();
        this.running = false;
        this.statusElement.textContent = "Нажми «Старт» или стрелку";
        this.updateScore();
        this.draw();
    }

    start() {
        if (this.running) {
            return;
        }
        this.running = true;
        this.statusElement.textContent = "Игра идёт";
        this.timer = setInterval(() => this.tick(), TICK_MS);
    }

    stop() {
        this.running = false;
        if (this.timer !== null) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    setDirection(direction) {
        if (!direction) {
            return;
        }
        if (direction.x === -this.direction.x && direction.y === -this.direction.y) {
            return;
        }
        if (direction.x === -this.nextDirection.x && direction.y === -this.nextDirection.y) {
            return;
        }
        this.nextDirection = direction;
        if (!this.running) {
            this.start();
        }
    }

    tick() {
        this.direction = this.nextDirection;
        const head = this.snake[0];
        const nextHead = {
            x: head.x + this.direction.x,
            y: head.y + this.direction.y,
        };

        if (this.isCollision(nextHead)) {
            this.stop();
            this.statusElement.textContent = "Игра окончена — нажми «Новая игра»";
            this.draw();
            return;
        }

        this.snake.unshift(nextHead);
        if (nextHead.x === this.food.x && nextHead.y === this.food.y) {
            this.score += 1;
            this.food = this.createFood();
            this.updateScore();
        } else {
            this.snake.pop();
        }

        this.draw();
    }

    isCollision(position) {
        if (
            position.x < 0 ||
            position.x >= GRID_SIZE ||
            position.y < 0 ||
            position.y >= GRID_SIZE
        ) {
            return true;
        }

        const bodyToCheck = this.snake.slice(0, -1);
        return bodyToCheck.some(
            (segment) => segment.x === position.x && segment.y === position.y,
        );
    }

    createFood() {
        const freeCells = [];
        for (let y = 0; y < GRID_SIZE; y += 1) {
            for (let x = 0; x < GRID_SIZE; x += 1) {
                if (!this.snake?.some((segment) => segment.x === x && segment.y === y)) {
                    freeCells.push({ x, y });
                }
            }
        }

        if (freeCells.length === 0) {
            this.stop();
            this.statusElement.textContent = "Победа! Поле заполнено";
            return { x: 0, y: 0 };
        }

        return freeCells[Math.floor(Math.random() * freeCells.length)];
    }

    updateScore() {
        this.scoreElement.textContent = String(this.score);
    }

    draw() {
        const { context, canvas, cellSize } = this;
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = "#111827";
        context.fillRect(0, 0, canvas.width, canvas.height);

        context.strokeStyle = "#1f2937";
        context.lineWidth = 1;
        for (let i = 1; i < GRID_SIZE; i += 1) {
            const offset = i * cellSize;
            context.beginPath();
            context.moveTo(offset, 0);
            context.lineTo(offset, canvas.height);
            context.stroke();
            context.beginPath();
            context.moveTo(0, offset);
            context.lineTo(canvas.width, offset);
            context.stroke();
        }

        this.drawCell(this.food, "#ef4444", 3);
        this.snake.forEach((segment, index) => {
            this.drawCell(segment, index === 0 ? "#a3e635" : "#65a30d", 3);
        });
    }

    drawCell(cell, fillStyle, radius) {
        const x = cell.x * this.cellSize + 2;
        const y = cell.y * this.cellSize + 2;
        const size = this.cellSize - 4;
        const context = this.context;

        context.fillStyle = fillStyle;
        context.beginPath();
        context.roundRect(x, y, size, size, radius);
        context.fill();
    }
}

export function bindSnakeControls(game) {
    window.addEventListener("keydown", (event) => {
        const direction = DIRECTIONS[event.key];
        if (!direction) {
            return;
        }
        event.preventDefault();
        game.setDirection(direction);
    });
}
