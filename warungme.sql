-- -------------------------------------------------------------
-- TablePlus 26.10.0(776)
--
-- https://tableplus.com/
--
-- Database: warungme
-- Generation Time: 2026-09-12 10:07:14.0370
-- -------------------------------------------------------------


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


DROP TABLE IF EXISTS `auth`;
CREATE TABLE `auth` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(60) COLLATE utf8mb4_general_ci NOT NULL,
  `tipeUser` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `pass` varchar(60) COLLATE utf8mb4_general_ci NOT NULL,
  `totalPembelian` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `laporan`;
CREATE TABLE `laporan` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nama` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `jumlah` int NOT NULL,
  `total` int NOT NULL,
  `tanggal` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS `tbbarang`;
CREATE TABLE `tbbarang` (
  `IdMenu` varchar(5) COLLATE utf8mb4_general_ci NOT NULL,
  `kategori` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `namaMenu` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `harga` int NOT NULL,
  `stock` int DEFAULT NULL,
  PRIMARY KEY (`IdMenu`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `auth` (`id`, `username`, `tipeUser`, `pass`, `totalPembelian`) VALUES
(1, 'andri', 'pembeli', 'andri26', 0);

INSERT INTO `laporan` (`id`, `nama`, `jumlah`, `total`, `tanggal`) VALUES
(1, 'Andri', 7, 200000, '2026-09-12 09:04:10'),
(28, 'Andri', 4, 46000, NULL),
(29, 'andri', 4, 74000, NULL),
(30, 'andri', 3, 31000, NULL),
(31, 'andri', 1, 8000, NULL),
(32, 'adsada', 1, 5000, NULL),
(33, 'sfsfs', 3, 31000, NULL),
(34, 'ddg', 2, 30000, NULL),
(35, 'andri', 2, 10000, NULL),
(36, 'adas', 2, 44000, NULL),
(37, 'sfesfs', 3, 35000, NULL),
(38, 'adssad', 3, 18000, NULL),
(39, 'andri', 2, 40000, NULL),
(40, 'Andri', 2, 30000, NULL),
(41, 'sefsfs', 4, 36000, NULL),
(42, 'dgdgd', 3, 21000, NULL),
(43, 'adasadsa', 3, 51000, NULL),
(44, 'sfsfsdfsd', 3, 25000, NULL),
(45, 'andri', 3, 21000, NULL),
(46, 'andri', 3, 21000, NULL),
(47, 'Andri', 5, 63000, NULL),
(48, 'hayyuk', 5, 51000, NULL),
(49, 'hantu', 4, 58000, NULL),
(50, 'boboi', 2, 36000, NULL),
(51, 'winarti', 5, 51000, NULL),
(52, 'Winter', 4, 50000, NULL),
(53, 'Qris', 2, 26000, NULL),
(54, 'Julian', 5, 62000, NULL),
(55, 'Andri', 3, 34000, NULL),
(56, 'Winter', 5, 47000, NULL),
(57, 'Tiren', 3, 18000, NULL),
(58, 'Weter', 5, 54000, NULL),
(59, 'n', 8, 72000, NULL),
(60, 'adit', 1, 22000, NULL),
(61, 'AndriE', 2, 23000, NULL),
(62, 'aditya', 1, 18000, NULL),
(63, 'www', 4, 88000, NULL),
(64, 'andri', 2, 44000, NULL),
(65, 'rahmatullah', 4, 52000, NULL),
(66, 'mm', 2, 10000, NULL),
(67, 'Andri', 3, 24400, NULL),
(68, 'andri', 2, 44000, '2026-09-12 09:05:34');

INSERT INTO `tbbarang` (`IdMenu`, `kategori`, `namaMenu`, `harga`, `stock`) VALUES
('AN001', 'Makanan', 'Mie Goreng', 20000, NULL),
('AN002', 'Makanan', 'Nasi Goreng', 22000, 1),
('AN003', 'Minuman', 'Es Teh', 5000, NULL),
('AN004', 'Minuman', 'Es Jeruk', 8000, NULL),
('AN005', 'Minuman', 'Jus Alpukat', 15000, NULL),
('AN006', 'Makanan', 'Mie Ayam', 18000, NULL),
('AN007', 'Makanan', 'Ayam Geprek', 22000, 1),
('AN008', 'Minuman', 'Matcha', 18000, NULL),
('AN009', 'Makanan', 'Kwetiaw', 3200, NULL),
('AN010', 'Minuman', 'Bakso', 16000, NULL),
('AN011', 'Minuman', 'Thai Tea', 30000, 100),
('AND01', 'Minuman', 'Teh Olong', 15000, NULL);



/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;