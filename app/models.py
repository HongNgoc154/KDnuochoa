from django.db import models

class SanPham(models.Model):
    id_SanPham = models.AutoField(primary_key=True)
    TenSanPham = models.CharField(max_length=255)
    MoTa_SanPham = models.TextField(null=True)
    TrangThai_SanPham = models.CharField(max_length=50)

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

    id_NhomHuong = models.ForeignKey(
        'NhomHuong',
        on_delete=models.DO_NOTHING,
        db_column='id_NhomHuong'
    )

    class Meta:
        managed = False
        db_table = 'SanPham'

    def __str__(self):
        return self.TenSanPham
    

class DungTich(models.Model):
    id_DungTich = models.AutoField(primary_key=True)
    GiaTri = models.CharField(max_length=50)  # 30ml, 50ml

    class Meta:
        managed = False
        db_table = 'DungTich'

    def __str__(self):
        return self.GiaTri


class BienThe(models.Model):
    id_BienThe = models.AutoField(primary_key=True)

    id_SanPham = models.ForeignKey(
    SanPham,
    on_delete=models.DO_NOTHING,
    db_column='id_SanPham'
)

    id_DungTich = models.ForeignKey(
        DungTich,
        on_delete=models.DO_NOTHING,
        db_column='id_DungTich'
    )

    GiaBan = models.DecimalField(max_digits=10, decimal_places=2)
    SoLuong = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'BienThe'




class LoaiSanPham(models.Model):
    id_LoaiSanPham = models.AutoField(primary_key=True)

    TenLoaiSanPham = models.CharField(
        max_length=255,
        db_column='TenLoaiSanPham'
    )

    class Meta:
        managed = False
        db_table = 'LoaiSanPham'

    def __str__(self):
        return self.TenLoaiSanPham


class ThuongHieu(models.Model):
    id_ThuongHieu = models.AutoField(primary_key=True)

    TenThuongHieu = models.CharField(
        max_length=255,
        db_column='TenThuongHieu'
    )

    class Meta:
        managed = False
        db_table = 'ThuongHieu'

    def __str__(self):
        return self.TenThuongHieu


class NhomHuong(models.Model):
    id_NhomHuong = models.AutoField(primary_key=True)

    TenNhomHuong = models.CharField(
        max_length=255,
        db_column='TenNhomHuong'
    )

    class Meta:
        managed = False
        db_table = 'NhomHuong'

    def __str__(self):
        return self.TenNhomHuong
    
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
        return self.GiaTri


class BienTheThuocTinh(models.Model):
    id_BienThe = models.ForeignKey(
        BienThe,
        on_delete=models.DO_NOTHING,
        db_column='id_BienThe'
    )

    id_GiaTriThuocTinh = models.ForeignKey(
        GiaTriThuocTinh,
        on_delete=models.DO_NOTHING,
        db_column='id_GiaTriThuocTinh'
    )

    class Meta:
        managed = False
        db_table = 'BienThe_ThuocTinh'
        unique_together = (('id_BienThe', 'id_GiaTriThuocTinh'),)

