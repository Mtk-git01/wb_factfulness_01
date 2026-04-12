library(shiny)
library(dplyr)
library(readr)
library(ggplot2)
library(DT)
library(leaflet)
library(sf)
library(rnaturalearth)
library(rnaturalearthdata)
library(countrycode)

# =========================
# 1. CSV
# =========================
perception_df_raw <- read_csv("world_getting_worse_extracted.csv", show_col_types = FALSE)
u5mr_df_raw <- read_csv("u5mr_country_year_all_countries.csv", show_col_types = FALSE)
completion_df_raw <- read_csv("girls_primary_completion_country_year.csv", show_col_types = FALSE)

# =========================
# 2. perception format
# =========================
perception_df <- perception_df_raw

if (!"country_iso3" %in% names(perception_df)) {
  if ("country" %in% names(perception_df)) {
    perception_df <- perception_df %>%
      mutate(
        country_iso3 = countrycode(country, origin = "country.name", destination = "iso3c")
      )
  } else {
    stop("world_getting_worse_extracted.csv must contain either 'country' or 'country_iso3'.")
  }
}

if (!"country" %in% names(perception_df)) {
  perception_df <- perception_df %>%
    mutate(
      country = countrycode(country_iso3, origin = "iso3c", destination = "country.name")
    )
}

if (!"pct_answered_world_getting_worse" %in% names(perception_df)) {
  stop("world_getting_worse_extracted.csv must contain 'pct_answered_world_getting_worse'.")
}

# =========================
# 3. U5MR format
# =========================
u5mr_df <- u5mr_df_raw %>%
  rename(
    country_iso3 = country_iso,
    country = country_name,
    u5mr = u5mr_estimate,
    standard_error = standard_error_of_estimates
  ) %>%
  mutate(
    year = as.integer(year),
    is_interpolated = as.logical(is_interpolated),
    `95% CI Lower` = ifelse(!is.na(standard_error), u5mr - 1.96 * standard_error, NA_real_),
    `95% CI Upper` = ifelse(!is.na(standard_error), u5mr + 1.96 * standard_error, NA_real_)
  )

# =========================
# 4. Girls primary completion format
# =========================
completion_names <- names(completion_df_raw)
print(completion_names)

if (!"country_name" %in% completion_names) {
  stop(
    paste0(
      "girls_primary_completion_country_year.csv must contain 'country_name'. Found columns: ",
      paste(completion_names, collapse = ", ")
    )
  )
}

if (!"country_iso" %in% completion_names) {
  stop(
    paste0(
      "girls_primary_completion_country_year.csv must contain 'country_iso'. Found columns: ",
      paste(completion_names, collapse = ", ")
    )
  )
}

if (!"year" %in% completion_names) {
  stop("girls_primary_completion_country_year.csv must contain 'year'.")
}

if (!"value" %in% completion_names) {
  stop("girls_primary_completion_country_year.csv must contain 'value'.")
}

completion_df <- completion_df_raw %>%
  mutate(
    country = country_name,
    country_iso3 = country_iso,
    year = as.integer(year),
    completion_rate = as.numeric(value),
    indicator_code = if ("indicator_code" %in% names(.)) as.character(indicator_code) else NA_character_,
    indicator_name = if ("indicator" %in% names(.)) as.character(indicator) else "Primary completion rate, female"
  ) %>%
  filter(is.na(indicator_code) | indicator_code == "SE.PRM.CMPT.FE.ZS") %>%
  select(country, country_iso3, year, completion_rate, indicator_code, indicator_name)

# -------------------------
# linear interpolation 
# - by country
# - sort by year
# - only inner missing point
# - exclude the edge
# -------------------------
completion_df <- completion_df %>%
  group_by(country_iso3) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    completion_rate_raw = completion_rate,
    completion_rate = if (sum(!is.na(completion_rate)) >= 2) {
      approx(
        x = year[!is.na(completion_rate)],
        y = completion_rate[!is.na(completion_rate)],
        xout = year,
        method = "linear",
        rule = 1
      )$y
    } else {
      completion_rate
    },
    completion_interpolated = is.na(completion_rate_raw) & !is.na(completion_rate)
  ) %>%
  ungroup()

# =========================
# 5. world map
# =========================
world <- ne_countries(scale = "medium", returnclass = "sf") %>%
  st_transform(4326) %>%
  mutate(country_iso3 = iso_a3)

map_df <- world %>%
  left_join(
    perception_df %>%
      select(country_iso3, country, pct_answered_world_getting_worse),
    by = "country_iso3"
  )

# =========================
# 6. UI
# =========================
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      body {
        background: #f5f7fb;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        color: #1f2d3d;
      }
      .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 4px;
        color: #16202a;
      }
      .sub-title {
        font-size: 16px;
        color: #5c6b7a;
        margin-bottom: 18px;
      }
      .info-card {
        background: white;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        margin-bottom: 16px;
      }
      .section-title {
        font-size: 28px;
        font-weight: 700;
        color: #1f2d3d;
        margin-bottom: 8px;
      }
      .meta-title {
        font-size: 18px;
        font-weight: 600;
        color: #1f2d3d;
        margin-bottom: 10px;
      }
      .small-note {
        font-size: 13px;
        color: #6b7280;
        line-height: 1.5;
      }
      .leaflet-container {
        border-radius: 14px;
      }
      table {
        width: 100%;
      }
      .dataTables_wrapper {
        font-size: 13px;
      }
      .shiny-options-group {
        margin-bottom: 10px;
      }
    "))
  ),
  
  div(class = "main-title", "Negativity Instinct vs Human Development"),
  div(
    class = "sub-title",
    "Factfulness-inspired interactive dashboard with child survival and girls' education indicators"
  ),
  
  fluidRow(
    column(
      width = 7,
      div(
        class = "info-card",
        leafletOutput("world_map", height = 720)
      )
    ),
    column(
      width = 5,
      div(
        class = "info-card",
        div(class = "section-title", textOutput("selected_country_title")),
        tableOutput("perception_info")
      ),
      div(
        class = "info-card",
        radioButtons(
          "indicator_switch",
          "Select indicator",
          choices = c(
            "U5MR" = "u5mr",
            "Girls primary completion" = "completion"
          ),
          selected = "u5mr",
          inline = TRUE
        ),
        uiOutput("indicator_meta_title"),
        plotOutput("indicator_plot", height = 390),
        div(
          class = "small-note",
          textOutput("indicator_note")
        )
      ),
      div(
        class = "info-card",
        div(class = "meta-title", "Data sources and metadata"),
        tableOutput("metadata_info")
      )
    )
  )
)

# =========================
# 7. Server
# =========================
server <- function(input, output, session) {
  
  pal <- colorNumeric(
    palette = c("#fff7bc", "#fee391", "#fdb863", "#ef6548", "#b30000"),
    domain = map_df$pct_answered_world_getting_worse,
    na.color = "#d9d9d9"
  )
  
  output$world_map <- renderLeaflet({
    leaflet(map_df) %>%
      addProviderTiles("CartoDB.Positron") %>%
      addPolygons(
        layerId = ~country_iso3,
        fillColor = ~pal(pct_answered_world_getting_worse),
        color = "#8a8a8a",
        weight = 0.8,
        opacity = 1,
        fillOpacity = 0.9,
        highlightOptions = highlightOptions(
          weight = 2,
          color = "#2b2b2b",
          fillOpacity = 0.95,
          bringToFront = TRUE
        ),
        label = ~paste0(
          name_long,
          ifelse(
            is.na(pct_answered_world_getting_worse),
            "",
            paste0(" | Negativity Instinct ratio: ", round(pct_answered_world_getting_worse, 1), "%")
          )
        ),
        popup = ~paste0(
          "<b>", name_long, "</b><br>",
          "ISO3: ", country_iso3, "<br>",
          "Negativity Instinct ratio: ",
          ifelse(
            is.na(pct_answered_world_getting_worse),
            "N/A",
            paste0(round(pct_answered_world_getting_worse, 1), "%")
          )
        )
      ) %>%
      addLegend(
        pal = pal,
        values = ~pct_answered_world_getting_worse,
        title = "% saying world is getting worse",
        position = "bottomright",
        opacity = 0.9
      )
  })
  
  selected_country <- reactive({
    click <- input$world_map_shape_click
    
    iso3 <- if (is.null(click$id)) "THA" else click$id
    
    map_df %>%
      filter(country_iso3 == iso3) %>%
      slice(1)
  })
  
  output$selected_country_title <- renderText({
    df <- selected_country()
    req(nrow(df) > 0)
    paste0(df$name_long[1], " (", df$country_iso3[1], ")")
  })
  
  output$perception_info <- renderTable({
    df <- selected_country()
    req(nrow(df) > 0)
    
    data.frame(
      Item = c("Country", "ISO3", "Negativity Instinct ratio"),
      Value = c(
        df$name_long[1],
        df$country_iso3[1],
        ifelse(
          is.na(df$pct_answered_world_getting_worse[1]),
          "N/A",
          paste0(round(df$pct_answered_world_getting_worse[1], 1), "%")
        )
      )
    )
  }, colnames = FALSE)
  
  selected_u5mr <- reactive({
    df <- selected_country()
    req(nrow(df) > 0)
    iso3 <- df$country_iso3[1]
    
    u5mr_df %>%
      filter(country_iso3 == iso3) %>%
      arrange(year)
  })
  
  selected_completion <- reactive({
    df <- selected_country()
    req(nrow(df) > 0)
    iso3 <- df$country_iso3[1]
    
    completion_df %>%
      filter(country_iso3 == iso3) %>%
      arrange(year)
  })
  
  output$indicator_meta_title <- renderUI({
    if (input$indicator_switch == "u5mr") {
      div(
        class = "meta-title",
        "Under-five mortality rate (U5MR): deaths per 1,000 live births"
      )
    } else {
      div(
        class = "meta-title",
        "Primary completion rate, female (% of relevant age group)"
      )
    }
  })
  
  output$indicator_plot <- renderPlot({
    country_label <- selected_country()$name_long[1]
    
    if (input$indicator_switch == "u5mr") {
      df <- selected_u5mr()
      req(nrow(df) > 0)
      
      ggplot(df, aes(x = year, y = u5mr)) +
        geom_ribbon(
          data = df %>% filter(!is.na(`95% CI Lower`), !is.na(`95% CI Upper`)),
          aes(ymin = `95% CI Lower`, ymax = `95% CI Upper`),
          fill = "#d73027",
          alpha = 0.16,
          inherit.aes = TRUE
        ) +
        geom_line(color = "#c62828", linewidth = 1.3, na.rm = TRUE) +
        labs(
          title = paste("U5MR trend:", country_label),
          x = "Year",
          y = "Deaths per 1,000 live births"
        ) +
        theme_minimal(base_size = 13) +
        theme(
          plot.title = element_text(face = "bold", color = "#1f2d3d"),
          axis.title = element_text(color = "#1f2d3d"),
          panel.grid.minor = element_blank()
        )
      
    } else {
      df <- selected_completion()
      req(nrow(df) > 0)
      
      ggplot(df, aes(x = year, y = completion_rate)) +
        geom_line(color = "#1b9e77", linewidth = 1.3, na.rm = TRUE) +
        geom_point(
          data = df %>% filter(completion_interpolated),
          color = "#d95f02",
          size = 2.2,
          na.rm = TRUE
        ) +
        geom_hline(yintercept = 100, linetype = "dashed", color = "gray50") +
        scale_x_continuous(
          limits = c(1995, NA),
          breaks = seq(1995, max(df$year, na.rm = TRUE), by = 5)
        ) +
        labs(
          title = paste("Girls primary completion trend:", country_label),
          x = "Year",
          y = "% of relevant age group"
        ) +
        theme_minimal(base_size = 13) +
        theme(
          plot.title = element_text(face = "bold", color = "#1f2d3d"),
          axis.title = element_text(color = "#1f2d3d"),
          panel.grid.minor = element_blank()
        )
    }
  })
  
  output$indicator_note <- renderText({
    if (input$indicator_switch == "u5mr") {
      "U5MR measures the number of children dying before age 5 per 1,000 live births. Shaded band shows the 95% confidence interval when standard errors are available."
    } else {
      "Primary completion rate can exceed 100% because the numerator may include over-age and under-age entrants to the final grade, while the denominator is the population of official graduation age. Missing values inside a country series are linearly interpolated; edge missing values are left as missing. Orange dots indicate interpolated values."
    }
  })
  
  output$metadata_info <- renderTable({
    u5mr_country_df <- selected_u5mr()
    completion_country_df <- selected_completion()
    
    u5mr_interpolated_share <- if (nrow(u5mr_country_df) > 0 && any(!is.na(u5mr_country_df$is_interpolated))) {
      round(mean(u5mr_country_df$is_interpolated, na.rm = TRUE) * 100, 1)
    } else {
      NA
    }
    
    completion_interp_share <- if (nrow(completion_country_df) > 0) {
      round(mean(completion_country_df$completion_interpolated, na.rm = TRUE) * 100, 1)
    } else {
      NA
    }
    
    completion_latest <- if (nrow(completion_country_df) > 0) {
      completion_country_df %>%
        filter(!is.na(completion_rate)) %>%
        arrange(desc(year)) %>%
        slice(1)
    } else {
      data.frame()
    }
    
    data.frame(
      Item = c(
        "Perception data source",
        "U5MR data source",
        "U5MR interpolated share",
        "Girls completion data source",
        "Girls completion indicator code",
        "Girls completion interpolated share",
        "Latest girls completion value"
      ),
      Value = c(
        "Factfulness / Gapminder visualization based on YouGov and Ipsos MORI survey results",
        "UN Inter-agency Group for Child Mortality Estimation (UN IGME)",
        ifelse(is.na(u5mr_interpolated_share), "N/A", paste0(u5mr_interpolated_share, "%")),
        "UNESCO Institute for Statistics / World Bank indicator metadata",
        ifelse(
          nrow(completion_country_df) > 0 && any(!is.na(completion_country_df$indicator_code)),
          completion_country_df$indicator_code[which(!is.na(completion_country_df$indicator_code))[1]],
          "SE.PRM.CMPT.FE.ZS"
        ),
        ifelse(is.na(completion_interp_share), "N/A", paste0(completion_interp_share, "%")),
        ifelse(
          nrow(completion_latest) == 0,
          "N/A",
          paste0(round(completion_latest$completion_rate[1], 1), "% (", completion_latest$year[1], ")")
        )
      )
    )
  }, colnames = FALSE)
}

shinyApp(ui, server)