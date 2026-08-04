# **************************************************************************** #
#                                  COLORS                                      #
# **************************************************************************** #

RESET   := \033[0m
BOLD    := \033[1m

RED     := \033[31m
GREEN   := \033[32m
YELLOW  := \033[33m
BLUE    := \033[34m
MAGENTA := \033[35m
CYAN    := \033[36m
WHITE   := \033[37m

SUCCESS = @printf "$(GREEN)✔$(RESET) %s\n"
INFO    = @printf "$(CYAN)➜$(RESET) %s\n"
WARN    = @printf "$(YELLOW)⚠$(RESET) %s\n"
TITLE   = @printf "$(BOLD)$(MAGENTA)\n========== %s ==========\n$(RESET)"
# **************************************************************************** #
#                                   ASCII                                      #
# **************************************************************************** #

define spinner
( \
WIDTH=40; \
POS=0; \
DIR=1; \
DOTS=$$(printf '·%.0s' $$(seq 1 $$WIDTH)); \
trap 'exit 0' INT TERM; \
while true; do \
    EATEN=$$(printf '%*s' "$$POS" ""); \
    REMAIN=$${DOTS:$$((POS + 1))}; \
    if [ $$((POS % 2)) -eq 0 ]; then MOUTH="C"; else MOUTH="c"; fi; \
    printf "\r\033[K$(CYAN)%s <$(WHITE)%s$(YELLOW)%s$(WHITE)%s$(CYAN)>$(RESET)" \
        "$(1)" "$$EATEN" "$$MOUTH" "$$REMAIN"; \
    sleep 0.08; \
    POS=$$((POS + DIR)); \
    if [ $$POS -ge $$((WIDTH - 1)) ]; then DIR=-1; fi; \
    if [ $$POS -le 0 ]; then DIR=1; fi; \
done \
) & \
SPIN_PID=$$!; \
$(2); \
EXIT_CODE=$$?; \
kill $$SPIN_PID 2>/dev/null; \
wait $$SPIN_PID 2>/dev/null; \
if [ $$EXIT_CODE -eq 0 ]; then \
    printf "\r\033[K$(GREEN)✓ %s complete.$(RESET)\n" "$(1)"; \
else \
    printf "\r\033[K$(RED)✗ %s failed.$(RESET)\n" "$(1)"; \
fi; \
exit $$EXIT_CODE
endef

BANNER = \
printf "$(YELLOW)"; \
printf "██████╗  █████╗  ██████╗      ███╗   ███╗ █████╗ ███╗   ██╗\n"; \
printf "██╔══██╗██╔══██╗██╔════╝      ████╗ ████║██╔══██╗████╗  ██║\n"; \
printf "██████╔╝███████║██║     █████╗██╔████╔██║███████║██╔██╗ ██║\n"; \
printf "██╔═══╝ ██╔══██║██║     ╚════╝██║╚██╔╝██║██╔══██║██║╚██╗██║\n"; \
printf "██║     ██║  ██║╚██████╗      ██║ ╚═╝ ██║██║  ██║██║ ╚████║\n"; \
printf "╚═╝     ╚═╝  ╚═╝ ╚═════╝      ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝\n"; \
printf "$(RESET)\n";

MLXBANNER = \
printf "$(BLUE)"; \
printf "███╗   ███╗██╗     ██╗  ██╗\n"; \
printf "████╗ ████║██║     ╚██╗██╔╝\n"; \
printf "██╔████╔██║██║      ╚███╔╝ \n"; \
printf "██║╚██╔╝██║██║      ██╔██╗ \n"; \
printf "██║ ╚═╝ ██║███████╗██╔╝ ██╗\n"; \
printf "╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝\n"; \
printf "$(RESET)\n";


# **************************************************************************** #
#                                 Variables                                    #
# **************************************************************************** #
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

MLX_DIR := minilibx-linux
MLX_REPO := https://github.com/42school/mlx_CLXV.git


# **************************************************************************** #
#                                  Actions                                     #
# **************************************************************************** #

all: install

install: banner mlx
	@printf "$(CYAN)"
	@printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
	@printf "        Preparing the environement\n"
	@printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
	@printf "$(RESET)"

	@test -d $(VENV) || python3 -m venv $(VENV)

	@$(PIP) install --upgrade pip >/dev/null

	@$(PIP) install build >/dev/null

	@$(call spinner,Installing dependencies,$(PIP) install -e . >/dev/null)

	@$(PIP) install flake8-pyproject mypy >/dev/null

	@$(call spinner,Installing MLX,$(PIP) install $(MLX_DIR)/*.whl >/dev/null)

	@$(MAKE) package-install

	@printf "\n$(GREEN)🗝  The maze is ready. Good luck!$(RESET)\n"


banner:
	@$(BANNER)
	@printf "$(CYAN)═══════════════════════════════════════════════$(RESET)\n"
	@printf "$(GREEN)   Welcome to Pac-Man!$(RESET)\n"
	@printf "$(YELLOW)   Every maze has an exit... find yours.$(RESET)\n"
	@printf "$(CYAN)═══════════════════════════════════════════════$(RESET)\n\n"


mlx:
	@$(MLXBANNER)
	@printf "$(CYAN)"
	@printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
	@printf "        Preparing the graphics engine\n"
	@printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
	@printf "$(RESET)"

	@if [ ! -d "$(MLX_DIR)" ]; then \
		printf "$(YELLOW)Summoning MiniLibX...$(RESET)\n"; \
		git clone $(MLX_REPO) $(MLX_DIR) >/dev/null 2>&1; \
	fi

	@$(call spinner,Building MiniLibX,$(MAKE) -s -C $(MLX_DIR) >/dev/null 2>&1)

	@printf "\n$(GREEN)"
	@printf "MiniLibX is ready to render the maze.\n"
	@printf "$(RESET)"


package-install:
	@$(call spinner,Installing libs package, $(PIP) install libs/*.whl --force-reinstall >/dev/null)
	@$(call spinner,Installing others package, $(PIP) install *.whl --force-reinstall >/dev/null)


run:
	@printf "$(BLUE)"
	@printf "╔══════════════════════════════════════╗\n"
	@printf "║         Entering the Maze...         ║\n"
	@printf "╚══════════════════════════════════════╝\n"
	@printf "$(RESET)"

	@$(PYTHON) pacman.py config.json

debug:
	$(TITLE) "Debug mode"
	$(PYTHON) -m pdb pacman.py config.json

lint:
	$(TITLE) "Running lint checks"
	@printf "$(BLUE)"
	@printf "╔══════════════════════════════════════╗\n"
	@printf "║             Flake Check ...          ║\n"
	@printf "╚══════════════════════════════════════╝\n"
	@printf "$(RESET)"
	-flake8 --exclude=.git,__pycache__,.venv,venv,minilibx-linux .
	@printf "$(BLUE)"
	@printf "╔══════════════════════════════════════╗\n"
	@printf "║              Mypy Check ...          ║\n"
	@printf "╚══════════════════════════════════════╝\n"
	@printf "$(RESET)"
	mypy .
	$(SUCCESS) "Lint complete!"

clean:
	$(TITLE) "Cleaning project"
	rm -rf */__pycache__
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	@if [ -d "$(MLX_DIR)" ]; then \
		$(MAKE) -C $(MLX_DIR) clean; \
	fi
	rm -f save_scores.json
	$(SUCCESS) "Clean complete!"

fclean: clean
	$(TITLE) "Full clean"
	rm -rf minilibx-linux
	rm -f *.whl
	rm -f *.tar.gz
	rm -rf .venv
	$(SUCCESS) "Everything removed!"

re: fclean install

.PHONY: all install mlx build run debug lint clean fclean