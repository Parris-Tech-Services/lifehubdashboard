.PHONY: refresh-all refresh-indexes refresh-text-games stats wellbeing recent

refresh-all:
	@bash scripts/refresh_all.sh

refresh-indexes:
	@bash scripts/refresh_indexes.sh

refresh-text-games:
	@python3 scripts/build_text_game_sources.py

stats:
	@python3 scripts/update_dashboard_stats.py

wellbeing:
	@python3 scripts/update_welltory_summary.py

recent:
	@python3 scripts/generate_recent_files.py

downloads:
	@python3 scripts/generate_downloads_feed.py
