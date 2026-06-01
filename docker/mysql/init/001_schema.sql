CREATE DATABASE IF NOT EXISTS test_cases_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE test_cases_db;

CREATE TABLE IF NOT EXISTS file_common_table (
  file_id VARCHAR(32) PRIMARY KEY,
  file_source VARCHAR(128) NOT NULL,
  skill_description VARCHAR(128) NOT NULL,
  file_path VARCHAR(512) NOT NULL,
  file_name VARCHAR(512) NOT NULL,
  upload_user_id VARCHAR(128),
  upload_user_name VARCHAR(128),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_testcase_generate_record (
  test_case_id VARCHAR(128) PRIMARY KEY,
  status VARCHAR(32) NOT NULL,
  message TEXT,
  is_comparison_done TINYINT(1) DEFAULT 0,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_testcase_generate_attachments (
  attachment_id VARCHAR(32) PRIMARY KEY,
  test_case_id VARCHAR(128) NOT NULL,
  download_url TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_attachments_test_case_id (test_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_evaluation_result (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  test_case_id VARCHAR(128) NOT NULL,
  file_id VARCHAR(32) NOT NULL,
  evaluation_result VARCHAR(128),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_evaluation_test_case_id (test_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS attachments_compare_result (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  test_case_id VARCHAR(128) NOT NULL,
  file_id VARCHAR(32) NOT NULL,
  file_type VARCHAR(128),
  file_sub_type VARCHAR(128),
  element_key VARCHAR(128),
  expected_value TEXT,
  parsed_value TEXT,
  similarity_score DECIMAL(8,2),
  match_status VARCHAR(64),
  handle_file_id VARCHAR(128),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_compare_test_case_id (test_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS comparison_info (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  test_case_id VARCHAR(128) NOT NULL,
  file_type VARCHAR(128),
  file_sub_type VARCHAR(128),
  element_key VARCHAR(128),
  element_name VARCHAR(128),
  comparison_count INT DEFAULT 0,
  correct_count INT DEFAULT 0,
  correct_percentage DECIMAL(8,2) DEFAULT 0,
  mistake_count INT DEFAULT 0,
  unclear_count INT DEFAULT 0,
  pass_or_not VARCHAR(8),
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_comparison_test_case_id (test_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
