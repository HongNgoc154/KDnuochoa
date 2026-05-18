from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


# ===================== NHÓM HƯƠNG =====================
class NhomHuong(models.Model):
    id_NhomHuong = models.AutoField(primary_key=True)

    TenNhomHuong = models.CharField(max_length=255)
    LoaiHuong = models.CharField(max_length=50, null=True, blank=True)
    IconUrl = models.ImageField(upload_to='scents/', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'NhomHuong'

    def __str__(self):
        return self.TenNhomHuong


# ===================== SẢN PHẨM =====================
class SanPham(models.Model):
    id_SanPham = models.AutoField(primary_key=True)
    TenSanPham = models.CharField(max_length=255)
    MoTa_SanPham = RichTextUploadingField()
    TrangThai_SanPham = models.CharField(max_length=50, null=True, blank=True)
    NongDo = models.CharField(max_length=50, null=True, blank=True)
    DoLuuHuong = models.IntegerField(null=True, blank=True)
    DoToaHuong = models.IntegerField(null=True, blank=True)
    MuaPhuHop = models.CharField(max_length=100, null=True, blank=True)
    ThoiDiemSuDung = models.CharField(max_length=100, null=True, blank=True)
    PhongCach = models.CharField(max_length=255, null=True, blank=True)
    DoTuoiPhuHop = models.CharField(max_length=100, null=True, blank=True)
    NamPhatHanh = models.IntegerField(null=True, blank=True)
    XuatXu = models.CharField(max_length=100, null=True, blank=True)

    id_ThuongHieu = models.ForeignKey(
        'ThuongHieu',
        on_delete=models.DO_NOTHING,
        db_column='id_ThuongHieu'
    )

    id_LoaiSanPham = models.ForeignKey(
        'LoaiSanPham',
        on_delete=models.DO_NOTHING,
        db_column='id_LoaiSanPham'
    )

    # ✅ FIX: dùng ManyToMany đơn giản (KHÔNG dùng through)
    nhom_huongs = models.ManyToManyField(
    NhomHuong,
    through='SanPhamNhomHuong',
    related_name='san_phams'
)

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        managed = False
        db_table = 'SanPham'

    def __str__(self):
        return self.TenSanPham


class SanPhamNhomHuong(models.Model):
    id = models.AutoField(primary_key=True)

    id_SanPham = models.ForeignKey(
        'SanPham',
        on_delete=models.DO_NOTHING,
        db_column='id_SanPham'
    )

    id_NhomHuong = models.ForeignKey(
        'NhomHuong',
        on_delete=models.DO_NOTHING,
        db_column='id_NhomHuong'
    )
    VaiTroHuong = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'SanPham_NhomHuong'

# ===================== BIẾN THỂ =====================
class BienThe(models.Model):
    id_BienThe = models.AutoField(primary_key=True)

    id_SanPham = models.ForeignKey(
        SanPham,
        on_delete=models.DO_NOTHING,
        db_column='id_SanPham'
    )

    Sku = models.CharField(max_length=100)
    GiaNhap = models.DecimalField(max_digits=10, decimal_places=2)
    GiaBan = models.DecimalField(max_digits=10, decimal_places=2)
    SoLuong = models.IntegerField()

    class Meta:
        verbose_name = "Biến thể"
        verbose_name_plural = "Biến thể"
        managed = False
        db_table = 'BienThe'

    def __str__(self):
        return f"{self.id_SanPham.TenSanPham} - {self.Sku}"


# ===================== LOẠI SẢN PHẨM =====================
class LoaiSanPham(models.Model):
    id_LoaiSanPham = models.AutoField(primary_key=True)

    TenLoaiSanPham = models.CharField(max_length=255)
    HinhanhUrl = models.ImageField(upload_to='categories/', null=True, blank=True)

    MoTa = models.TextField(null=True, blank=True)
    GhiChu = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'LoaiSanPham'

    def __str__(self):
        return self.TenLoaiSanPham


# ===================== THƯƠNG HIỆU =====================
class ThuongHieu(models.Model):
    id_ThuongHieu = models.AutoField(primary_key=True)

    TenThuongHieu = models.CharField(max_length=255)
    LogoUrl = models.ImageField(upload_to='brands/', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ThuongHieu'

    def __str__(self):
        return self.TenThuongHieu


# ===================== HÌNH ẢNH =====================
class HinhAnh(models.Model):
    id_HinhAnh = models.AutoField(primary_key=True)

    url = models.ImageField(upload_to='products/', null=True, blank=True)

    id_SanPham = models.ForeignKey(
        SanPham,
        on_delete=models.DO_NOTHING,
        db_column='id_SanPham',
        null=True,
        blank=True,
    )

    id_BienThe = models.ForeignKey(
        BienThe,
        on_delete=models.DO_NOTHING,
        db_column='id_BienThe',
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = 'HinhAnh'


# ===================== BÀI VIẾT =====================
class BaiViet(models.Model):
    id_BaiViet = models.AutoField(primary_key=True)
    TieuDe = models.CharField(max_length=255)
    NoiDung = models.TextField(null=True)
    NgayTao = models.DateTimeField(null=True)
    TacGia = models.CharField(max_length=255, null=True)
    AnhDaiDien = models.ImageField(upload_to='blog/', null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'BaiViet'


# ===================== THUỘC TÍNH =====================
class ThuocTinh(models.Model):
    id_ThuocTinh = models.AutoField(primary_key=True)
    TenThuocTinh = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'ThuocTinh'

    def __str__(self):
        return self.TenThuocTinh


class GiaTriThuocTinh(models.Model):
    id_GiaTriThuocTinh = models.AutoField(primary_key=True)

    id_ThuocTinh = models.ForeignKey(
        ThuocTinh,
        on_delete=models.DO_NOTHING,
        db_column='id_ThuocTinh'
    )

    GiaTri = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'GiaTriThuocTinh'

    def __str__(self):
        return f"{self.id_ThuocTinh.TenThuocTinh}: {self.GiaTri}"


class BienTheThuocTinh(models.Model):
    id = models.AutoField(primary_key=True)

    id_BienThe = models.ForeignKey(
        'BienThe',
        on_delete=models.DO_NOTHING,
        db_column='id_BienThe'
    )

    id_GiaTriThuocTinh = models.ForeignKey(
        'GiaTriThuocTinh',
        on_delete=models.DO_NOTHING,
        db_column='id_GiaTriThuocTinh'
    )

    class Meta:
        managed = False
        db_table = 'BienThe_ThuocTinh'


# ===================== TÀI KHOẢN =====================
class TaiKhoan(models.Model):
    id_TaiKhoan = models.AutoField(primary_key=True)
    Username = models.CharField(max_length=100, null=True)
    MatKhau = models.CharField(max_length=255, null=True)
    TenDangNhap = models.CharField(max_length=255, null=True)
    Email = models.CharField(max_length=255, null=True)
    SDT = models.CharField(max_length=20, null=True)
    LoaiTaiKhoan = models.CharField(max_length=50, null=True)
    TrangThai_TaiKhoan = models.CharField(max_length=50, null=True)
    NgayTao = models.DateTimeField(null=True)
    DiemTichLuy = models.IntegerField(default=0)
    TongChiTieu = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    HangThanhVien = models.CharField(max_length=50, default='Silver')
    AnhDaiDien = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = "TaiKhoan"


# ===================== KHUYẾN MÃI =====================

class KhuyenMai(models.Model):

    id_KhuyenMai = models.AutoField(primary_key=True)

    MaKhuyenMai = models.CharField(max_length=50, null=True, blank=True)

    TenKhuyenMai = models.CharField(max_length=255, null=True, blank=True)

    MoTa = models.TextField(null=True, blank=True)

    LoaiKhuyenMai = models.CharField(max_length=50, null=True, blank=True)

    LoaiGiam = models.CharField(max_length=20, null=True, blank=True)

    GiaTriGiam = models.FloatField(null=True, blank=True)

    GiamToiDa = models.FloatField(null=True, blank=True)

    DonHangToiThieu = models.FloatField(null=True, blank=True)

    SoLuong = models.IntegerField(null=True, blank=True)

    DaSuDung = models.IntegerField(default=0)

    NgayBatDau = models.DateTimeField(null=True, blank=True)

    NgayKetThuc = models.DateTimeField(null=True, blank=True)

    TrangThai = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'KhuyenMai'

    def __str__(self):
        return self.MaKhuyenMai


# ===================== KHUYẾN MÃI TÀI KHOẢN =====================

class KhuyenMaiTaiKhoan(models.Model):

    id = models.AutoField(primary_key=True)

    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.DO_NOTHING,
        db_column='id_TaiKhoan'
    )

    id_KhuyenMai = models.ForeignKey(
        'KhuyenMai',
        on_delete=models.DO_NOTHING,
        db_column='id_KhuyenMai'
    )

    DaSuDung = models.BooleanField(default=False)

    NgayNhan = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'KhuyenMai_TaiKhoan'


class DonHang(models.Model):
    id_DonHang = models.AutoField(primary_key=True)

    MaDonHang = models.CharField(max_length=100, null=True, blank=True)

    id_KhachHang = models.ForeignKey(
        'KhachHang',
        on_delete=models.DO_NOTHING,
        db_column='id_KhachHang',
        null=True,
        blank=True
    )
    id_GiaoHang = models.ForeignKey(
        'GiaoHang',
        on_delete=models.DO_NOTHING,
        db_column='id_GiaoHang',
        null=True,
        blank=True
    )

    ThoiGian            = models.DateTimeField(null=True)
    HinhThucThanhToan   = models.CharField(max_length=100, null=True, blank=True)
    TrangThai           = models.CharField(max_length=50, null=True)
    TongTien            = models.DecimalField(max_digits=12, decimal_places=2, null=True)

    # ── Điểm (có trong DB) ──
    DiemDaDung          = models.IntegerField(default=0, null=True)
    TienGiamTuDiem      = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True)
    DiemNhanDuoc        = models.IntegerField(default=0, null=True)

    class Meta:
        managed  = False
        db_table = 'DonHang'

    def __str__(self):
        return self.MaDonHang or str(self.id_DonHang)
    


# ===================== CHI TIẾT ĐƠN HÀNG =====================
class ChiTietDonHang(models.Model):
    id_ChiTietDon = models.AutoField(primary_key=True)

    id_DonHang = models.ForeignKey(
        'DonHang',
        on_delete=models.DO_NOTHING,
        db_column='id_DonHang',
        null=True,
        blank=True
    )
    id_BienThe = models.ForeignKey(
        'BienThe',
        on_delete=models.DO_NOTHING,
        db_column='id_BienThe',
        null=True,
        blank=True
    )
    SoLuong = models.IntegerField(null=True)
    GiaBan  = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    GiaGiam = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        managed  = False
        db_table = 'ChiTietDonHang'


# ===================== ĐÁNH GIÁ =====================
# ═══════════════════════════════════════════════════════════════
# Trong models.py — tìm class DanhGia và thay bằng đoạn dưới
# Xóa NgayTao vì bảng DB không có cột này
# ═══════════════════════════════════════════════════════════════

# ===================== ĐÁNH GIÁ =====================
class DanhGia(models.Model):
    id_DanhGia = models.AutoField(primary_key=True)

    id_SanPham = models.ForeignKey(
        'SanPham',
        on_delete=models.DO_NOTHING,
        db_column='id_SanPham',
        null=True,
        blank=True
    )

    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.DO_NOTHING,
        db_column='id_TaiKhoan',
        null=True,
        blank=True
    )

    parent_id = models.IntegerField(null=True, blank=True)

    SoSao = models.IntegerField(null=True)
    NoiDung = models.TextField(null=True)

    NgayDanhGia = models.DateTimeField(null=True, blank=True)
    # NgayTao đã bị xóa — bảng DanhGia trong DB không có cột này

    class Meta:
        managed = False
        db_table = 'DanhGia'


# ═══════════════════════════════════════════════════════════════
# 1. models.py — thay class LichSuDiem cho đúng DB thực tế
# DB có: id_LichSuDiem, id_TaiKhoan, SoDiem, Loai, MoTa, id_DonHang, NgayTao
# ═══════════════════════════════════════════════════════════════

class LichSuDiem(models.Model):
    id_LichSuDiem = models.AutoField(primary_key=True)

    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.DO_NOTHING,
        db_column='id_TaiKhoan'
    )
    id_DonHang = models.ForeignKey(
        'DonHang',
        on_delete=models.DO_NOTHING,
        db_column='id_DonHang',
        null=True, blank=True
    )
    SoDiem    = models.IntegerField()                            # cột thực trong DB
    Loai      = models.CharField(max_length=50)                  # cột thực trong DB
    MoTa      = models.CharField(max_length=255, null=True)
    NgayTao   = models.DateTimeField(null=True)

    class Meta:
        managed  = False
        db_table = 'LichSuDiem'


class CauHinhThanhVien(models.Model):
    id_CauHinh = models.AutoField(primary_key=True)
    Hang = models.CharField(max_length=50)
    MucChiTieuToiThieu = models.DecimalField(max_digits=14, decimal_places=2)
    QuyDoiDiem = models.IntegerField(default=100)  # 1 điểm = 100 VNĐ
    GioiHanDiemTheoPhanTram = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    ThuongDonDauTien = models.IntegerField(default=200)
    ThuongDanhGia = models.IntegerField(default=100)
    QuyenLoi = models.TextField(null=True, blank=True)
    TrangThai = models.CharField(max_length=20, default='active')

    class Meta:
        managed = False
        db_table = 'CauHinhThanhVien'

# ===================== HỎI ĐÁP =====================
class HoiDap(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Đang chờ'),
        ('answered', 'Đã trả lời'),
        ('hidden', 'Ẩn'),
    )

    id_HoiDap = models.AutoField(primary_key=True)

    id_SanPham = models.ForeignKey(
        'SanPham',
        on_delete=models.DO_NOTHING,
        db_column='id_SanPham',
        null=True,
        blank=True
    )

    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.DO_NOTHING,
        db_column='id_TaiKhoan',
        null=True,
        blank=True
    )

    NoiDung = models.TextField(null=True)

    NgayTao = models.DateTimeField(null=True)

    parent_id = models.IntegerField(null=True, blank=True)

    TrangThai = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        managed = False
        db_table = 'HoiDap'


# ===================== GIAO HÀNG =====================
class GiaoHang(models.Model):
    id_GiaoHang  = models.AutoField(primary_key=True)
    id_TaiKhoan  = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.DO_NOTHING,
        db_column='id_TaiKhoan',
        null=True, blank=True
    )
    TenNguoiNhan = models.CharField(max_length=255, null=True)
    SDT          = models.CharField(max_length=20, null=True)
    DiaChi       = models.TextField(null=True)
    GhiChu       = models.TextField(null=True)
 
    class Meta:
        managed  = False
        db_table = 'GiaoHang'


# ===================== KHÁCH HÀNG =====================
class KhachHang(models.Model):
    id_KhachHang = models.AutoField(primary_key=True)
    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.CASCADE,
        db_column='id_TaiKhoan',
        null=True
    )
    TenKhachHang = models.CharField(max_length=255, null=True)
    # Email = models.CharField(max_length=255, null=True)
    # SDT = models.CharField(max_length=20, null=True)
    DiaChi = models.CharField(max_length=255, null=True)
    GioiTinh = models.CharField(max_length=10, null=True)

    class Meta:
        managed = False
        db_table = 'KhachHang'

    def __str__(self):
        return self.TenKhachHang or f"KH {self.id_KhachHang}"
    


# ═══════════════════════════════════════════════════════════════
# 1. models.py — thay class YeuThich
# ═══════════════════════════════════════════════════════════════

class YeuThich(models.Model):
    id_YeuThich = models.AutoField(primary_key=True)

    id_TaiKhoan = models.ForeignKey(
        'TaiKhoan',
        on_delete=models.CASCADE,
        db_column='id_TaiKhoan'
    )

    id_SanPham = models.ForeignKey(
        'SanPham',
        on_delete=models.CASCADE,
        db_column='id_SanPham'
    )

    class Meta:
        managed         = False
        db_table        = 'YeuThich'
        unique_together = [('id_TaiKhoan', 'id_SanPham')]