
# setup ---------------------------------------------------------------------------------------
source("C:/Users/jeffb/Desktop/Life/personal-projects/util.R")
setwd('C:/Users/jeffb/Desktop/Life/personal-projects/spotify')

listening_history = fread('track_data/users/jeff/listening_history.csv')
track_analysis = fread('track_data/users/jeff/listening_history_analysis.csv')
# library = 

reformat_time = function(x){ 
  
  x_real = case_when(x >= 1300 & x <= 2400 ~ x - 1200,
                     x >= 2400 ~ x - 2300,
                     TRUE ~ x) |> 
    as.character() %>% 
    str_pad(., width = 4, pad = '0')
  
  x_reformatted = str_c(substr(x_real, start = 1, stop = 2), ':',
                        substr(x_real, start = 3, stop = 4)
  )
  
  output = ifelse(x > 2400 | x < 1200, str_c(x_reformatted, ' AM'), str_c(x_reformatted, ' PM'))
  
  return(output)
}
# clean ---------------------------------------------------------------------------------------
genre_normalization = track_analysis |> 
  select(track_id, genres) |>
  separate(genres, into = paste0('genre_', seq(1, 25)), sep = ',') |> 
  mutate(across(everything(), ~str_replace_all(., "\\'|\\[|\\]", ''))) |>
  pivot_longer(!track_id) |>
  mutate(value = str_squish(value)) |> 
  mutate(value = ifelse(value == '', NA, value)) |> 
  filter(!is.na(value)) |> 
  group_by(value) |> 
  mutate(n = n()) |>
  ungroup() |> 
  group_by(track_id) |> 
  mutate(genre_keep = n == max(n)) |> 
  filter(genre_keep) |> 
  slice(1) |> 
  rename(genre = value)

analysis_combined = listening_history |> 
  inner_join(track_analysis |> select(-artist_id), by = c('track_id')) |> 
  mutate(listening_hour = hour(timestamp)) |> 
  mutate(listening_time = as.integer(format(timestamp, "%H%M"))) |> 
  mutate(listening_day = as.Date(timestamp)) |> 
  mutate(listening_day_of_week = weekdays(timestamp)) |> 
  mutate(listening_day_of_week = factor(listening_day_of_week, levels = c('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))) |> 
  mutate(listening_period = case_when(listening_time >= 300 & listening_time < 800 ~ 'Sleep',
                                      listening_time >= 800 & listening_time < 1700 ~ 'Work',
                                      listening_time >= 1700 | listening_time < 300 ~ 'Play')
         ) |> 
  mutate(listening_period = factor(listening_period, levels = c('Sleep', 'Work', 'Play'))) |> 
  mutate(listening_time = ifelse(listening_time < 300, listening_time + 2400, listening_time)) |> 
  mutate(listening_time_formatted = reformat_time(listening_time)) |> 
  relocate(listening_time_formatted, .after = 'timestamp') |>
  left_join(genre_normalization |> select(track_id, genre), by = 'track_id')


# week plots ----------------------------------------------------------------------------------
## scatter plot  -------------------------------------------------------------------------------

# energy + valence by day of week
# todo make filled bands of valence
ggplot(analysis_combined,
       aes(x = listening_time,
           y = energy,
           color = valence)) +
  geom_point(size = 4, alpha = 0.5) +
  geom_smooth(color = 'gray50', fill = 'gray95') +
  # geom_boxplot() +
  # geom_line() + 
  scale_x_continuous(labels = function(x) reformat_time(x)) +
  coord_cartesian(ylim = c(0, 1)) +
  scale_color_gradient(low = 'salmon', high = 'dodgerblue') +
  facet_grid(rows = vars(listening_day_of_week),
             cols = vars(listening_period),
             scales = 'free') +
  theme_pubr(border = TRUE)



## boxplot -------------------------------------------------------------------------------------
analysis_combined |> 
  group_by(listening_day, listening_hour) |> 
  mutate(time_listened = sum(duration_ms) / 1000 / 60) |> 
  ungroup() %>%
ggplot(.,
       aes(x = as.factor(listening_hour),
           y = energy,
           fill = time_listened)) +
  geom_boxplot() +
  # geom_point(size = 4, alpha = 0.5) +
  # geom_smooth(color = 'gray50', fill = 'gray95') +
  # geom_boxplot() +
  # geom_line() + 
  # scale_x_continuous(labels = function(x) reformat_time(x)) +
  coord_cartesian(ylim = c(0, 1)) +
  scale_color_gradient(low = 'salmon', high = 'dodgerblue') +
  facet_grid(rows = vars(listening_day_of_week),
             cols = vars(listening_period),
             scales = 'free') +
  theme_pubr(border = TRUE)





# time listened  ------------------------------------------------------------------------------
analysis_combined |>
  filter(listening_day >= Sys.Date() - days(7)) |> 
  group_by(listening_day, listening_period) |> 
  summarize(time_listened = sum(duration_ms / 1000 / 60),
            valence = mean(valence)) %>% 
  ggplot(.,
         aes(x = listening_day,
             y = time_listened,
             group = 1,
             fill = listening_period)
        ) +
  geom_bar(stat = 'identity') +
  geom_text(aes(label = glue('{round(time_listened, 0)} min')),
            position = position_stack(vjust = 0.5)
            ) +
  scale_x_date(breaks = 'days', date_labels = '%B %d\n%A') +
  labs(y = 'Time Listened (min)') +
  theme_pubr() + 
  theme(axis.title.x = element_blank()) + 
  theme(legend.position = 'none')


ggplot(analysis_combined, 
       aes(x = timestamp,
           y = ))

# listening table -----------------------------------------------------------------------------
analysis_combined |> 
  group_by(track_id) |> 
  summarize(times_listened = n()) |> 
  arrange(desc(times_listened)) |> 
  right_join(analysis_combined |> select(track_id, track, artist, genre, energy, valence)) |> 
  distinct() |> 
  select(-track_id) |> 
  relocate(times_listened, .after = 'genre') |> 
  DT::datatable()
