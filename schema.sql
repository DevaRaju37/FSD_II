CREATE DATABASE IF NOT EXISTS movie_booking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE movie_booking;

DROP TABLE IF EXISTS booking_seats;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS shows;
DROP TABLE IF EXISTS theatres;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE movies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  genre VARCHAR(100),
  duration VARCHAR(30),
  language VARCHAR(50),
  rating VARCHAR(10),
  description TEXT,
  poster_url VARCHAR(500),
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE theatres (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  location VARCHAR(200) NOT NULL
);

CREATE TABLE shows (
  id INT AUTO_INCREMENT PRIMARY KEY,
  movie_id INT NOT NULL,
  theatre_id INT NOT NULL,
  show_date DATE NOT NULL,
  show_time TIME NOT NULL,
  price DECIMAL(8,2) NOT NULL,
  FOREIGN KEY (movie_id) REFERENCES movies(id),
  FOREIGN KEY (theatre_id) REFERENCES theatres(id),
  UNIQUE KEY unique_show (movie_id,theatre_id,show_date,show_time)
);

CREATE TABLE seats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  theatre_id INT NOT NULL,
  seat_number VARCHAR(8) NOT NULL,
  seat_type ENUM('REGULAR','PREMIUM') DEFAULT 'REGULAR',
  FOREIGN KEY (theatre_id) REFERENCES theatres(id),
  UNIQUE KEY unique_theatre_seat (theatre_id,seat_number)
);

CREATE TABLE bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  show_id INT NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status ENUM('PENDING','CONFIRMED','CANCELLED') NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (show_id) REFERENCES shows(id)
);

CREATE TABLE booking_seats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT NOT NULL,
  seat_id INT NOT NULL,
  FOREIGN KEY (booking_id) REFERENCES bookings(id),
  FOREIGN KEY (seat_id) REFERENCES seats(id),
  UNIQUE KEY unique_booking_seat (booking_id,seat_id)
);

CREATE TABLE payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  payment_method VARCHAR(30) NOT NULL,
  status ENUM('SUCCESS','FAILED','REFUNDED') NOT NULL,
  transaction_ref VARCHAR(80) DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

INSERT INTO movies(title,genre,duration,language,rating,description,poster_url) VALUES
('The Last Horizon','Adventure / Sci-Fi','2h 18m','English','8.4','A group of explorers discovers an unexpected signal beyond the solar system.','https://image.tmdb.org/t/p/w500/8b8R8lZ5k8k5k5k5k5k5k5k5k5k.jpg'),
('City of Dreams','Drama','2h 05m','Telugu','7.9','An aspiring artist follows a difficult path to make a place in a busy city.','https://image.tmdb.org/t/p/w500/example-poster-2.jpg'),
('The Hidden Code','Thriller','1h 56m','Hindi','8.1','A young programmer uncovers a mystery hidden inside a forgotten system.','https://image.tmdb.org/t/p/w500/example-poster-3.jpg');

INSERT INTO theatres(name,location) VALUES
('CineMax Multiplex','Bhimavaram, Andhra Pradesh'),
('Galaxy Cinemas','Vijayawada, Andhra Pradesh');

-- 40 sample seats for each theatre (A-D rows, 1-10).
INSERT INTO seats(theatre_id,seat_number,seat_type)
SELECT t.id, CONCAT(r.row_name,n.num),
       IF(r.row_name IN ('A','B'),'PREMIUM','REGULAR')
FROM theatres t
CROSS JOIN (SELECT 'A' row_name UNION SELECT 'B' UNION SELECT 'C' UNION SELECT 'D') r
CROSS JOIN (
 SELECT 1 num UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5
 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9 UNION SELECT 10
) n;

INSERT INTO shows(movie_id,theatre_id,show_date,show_time,price) VALUES
(1,1,CURDATE() + INTERVAL 1 DAY,'10:00:00',180.00),
(1,1,CURDATE() + INTERVAL 1 DAY,'14:00:00',220.00),
(2,1,CURDATE() + INTERVAL 1 DAY,'18:30:00',200.00),
(3,2,CURDATE() + INTERVAL 2 DAY,'19:00:00',190.00);
