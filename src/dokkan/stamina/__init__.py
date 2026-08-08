"""ACT refills, shared by the modes that run out of stamina mid-farm.

Two flows, because the game offers two different screens for it: `level` for
the recovery menu a normal stage shows, `ztur` for the shorter one the ZTUR
stages show. Both read `use_meat_first` and `use_dragon_stones` from the config.
"""
