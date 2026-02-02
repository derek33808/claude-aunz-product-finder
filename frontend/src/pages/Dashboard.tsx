import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, Select, Image, Tooltip, Modal, Descriptions, Divider, Drawer, InputNumber, Slider, Switch, Rate, Spin, Alert } from 'antd';
import { ShoppingOutlined, RiseOutlined, FileTextOutlined, GlobalOutlined, ReloadOutlined, FireOutlined, LinkOutlined, SearchOutlined, PictureOutlined, EyeOutlined, CloseOutlined, DeleteOutlined, DownOutlined, UpOutlined, ExportOutlined, FileAddOutlined, ShopOutlined, DollarOutlined, CalculatorOutlined, CheckCircleOutlined, EnvironmentOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { productsApi, reportsApi, trendsApi, suppliersApi } from '../services/api';
import type { Product, Report, Supplier1688, SupplierMatchResult } from '../types';
import type { TableRowSelection } from 'antd/es/table/interface';

type HotProduct = Product & { hot_score: number };

const Dashboard = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState<any>(null);
  const [hotProducts, setHotProducts] = useState<HotProduct[]>([]);
  const [hotLoading, setHotLoading] = useState(false);
  const [selectedProductForTrend, setSelectedProductForTrend] = useState<string>('');
  const [trendLoading, setTrendLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<HotProduct | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<HotProduct[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [selectionPanelCollapsed, setSelectionPanelCollapsed] = useState(false);

  // 1688 Supplier matching state
  const [supplierDrawerVisible, setSupplierDrawerVisible] = useState(false);
  const [supplierMatchResults, setSupplierMatchResults] = useState<SupplierMatchResult[]>([]);
  const [supplierLoading, setSupplierLoading] = useState(false);
  const [supplierMaxPrice, setSupplierMaxPrice] = useState<number>(500);
  const [supplierLimit, setSupplierLimit] = useState<number>(10);
  const [includeLargeItems, setIncludeLargeItems] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier1688 | null>(null);
  const [profitModalVisible, setProfitModalVisible] = useState(false);
  const [profitQuantity, setProfitQuantity] = useState<number>(100);

  useEffect(() => { loadDashboardData(); }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const productData = await productsApi.search({ page_size: 10 });
      setProducts(productData);
      const reportData = await reportsApi.list({ page_size: 5 });
      setReports(reportData);
      try {
        const trends = await trendsApi.getInterest('wireless earbuds', 'AU');
        setTrendData(trends);
      } catch (e) { console.log('Trends not available'); }
    } catch (error) { console.error('Failed to load dashboard data:', error); }
    finally { setLoading(false); }
  };

  const platformColors: Record<string, string> = { ebay_au: 'blue', ebay_nz: 'green', amazon_au: 'orange', trademe: 'purple' };

  const findHotProducts = async () => {
    setHotLoading(true);
    try {
      const data = await productsApi.getHotProducts(10);
      setHotProducts(data);
    } catch (error) {
      console.error('Failed to get hot products:', error);
    } finally {
      setHotLoading(false);
    }
  };

  const loadTrendForProduct = async (productTitle: string) => {
    if (!productTitle) return;
    setTrendLoading(true);
    setSelectedProductForTrend(productTitle);
    try {
      const keyword = productTitle.split(' ').slice(0, 3).join(' ');
      const trends = await trendsApi.getInterest(keyword, 'AU');
      setTrendData(trends);
    } catch (e) {
      console.log('Trends not available for product');
    } finally {
      setTrendLoading(false);
    }
  };

  const getGoogleShoppingUrl = (product: Product) => {
    const query = encodeURIComponent(product.title);
    if (product.platform === 'ebay_nz' || product.platform === 'trademe') {
      return `https://www.google.co.nz/search?q=${query}&tbm=shop`;
    }
    return `https://www.google.com.au/search?q=${query}&tbm=shop`;
  };

  const getSalesDisplay = (product: HotProduct) => {
    const monthlySalesEst = product.review_count ? product.review_count * 25 : 0;
    if (product.sold_count) {
      return `${t('products.soldCount')}: ${product.sold_count} | ${t('products.monthlySalesEst')}: ~${monthlySalesEst}`;
    }
    return monthlySalesEst > 0 ? `${t('products.monthlySalesEst')}: ~${monthlySalesEst}` : '-';
  };

  const handleGenerateReport = async (product: HotProduct) => {
    try {
      await reportsApi.generate({
        title: 'Report: ' + product.title.substring(0, 50),
        report_type: 'quick',
        target_type: 'product',
        target_value: product.id,
      });
      // message.success(t('products.reportStarted'));
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  };

  const handleRemoveFromSelection = (productId: string) => {
    setSelectedProducts(prev => prev.filter(p => p.id !== productId));
    setSelectedRowKeys(prev => prev.filter(key => key !== productId));
  };

  const handleClearAllSelections = () => {
    setSelectedProducts([]);
    setSelectedRowKeys([]);
  };

  const handleExportSelected = () => {
    if (selectedProducts.length === 0) return;
    const exportData = selectedProducts.map(p => ({
      title: p.title,
      platform: p.platform,
      price: `${p.currency} ${Number(p.price).toFixed(2)}`,
      rating: p.rating,
      reviews: p.review_count,
      hot_score: p.hot_score,
      url: p.product_url || ''
    }));
    const csvContent = [
      Object.keys(exportData[0]).join(','),
      ...exportData.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `selected_products_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleGenerateComparisonReport = async () => {
    if (selectedProducts.length < 2) return;
    try {
      await reportsApi.generate({
        title: 'Comparison: ' + selectedProducts.map(p => p.title.substring(0, 20)).join(' vs '),
        report_type: 'comparison',
        target_type: 'keyword',
        target_value: selectedProducts.map(p => p.title).join(','),
      });
    } catch (error) {
      console.error('Failed to generate comparison report:', error);
    }
  };

  // 1688 Supplier matching functions
  const handleMatch1688Suppliers = async () => {
    if (selectedProducts.length === 0) return;

    setSupplierLoading(true);
    setSupplierDrawerVisible(true);
    setSupplierMatchResults([]);

    try {
      const results = await suppliersApi.match({
        product_ids: selectedProducts.map(p => p.id),
        max_price: supplierMaxPrice,
        limit: supplierLimit,
        include_large: includeLargeItems,
      });
      setSupplierMatchResults(results);
    } catch (error) {
      console.error('Failed to match suppliers:', error);
    } finally {
      setSupplierLoading(false);
    }
  };

  const calculateEstimatedProfit = (supplier: Supplier1688, sourceProduct: HotProduct) => {
    const exchangeRate = sourceProduct.currency === 'NZD' ? 0.233 : 0.213;
    const shippingPerUnit = 15; // CNY
    const totalCostCNY = (supplier.price + shippingPerUnit) * profitQuantity;
    const totalCostTarget = totalCostCNY * exchangeRate;
    const revenue = Number(sourceProduct.price) * profitQuantity;
    const grossProfit = revenue - totalCostTarget;
    const profitMargin = (grossProfit / revenue) * 100;
    const roi = (grossProfit / totalCostTarget) * 100;

    return {
      totalCostCNY,
      totalCostTarget: totalCostTarget.toFixed(2),
      revenue: revenue.toFixed(2),
      grossProfit: grossProfit.toFixed(2),
      profitMargin: profitMargin.toFixed(1),
      roi: roi.toFixed(1),
    };
  };

  const getSourceProductForSupplier = (productId: string): HotProduct | undefined => {
    return selectedProducts.find(p => p.id === productId);
  };

  const exportSupplierResults = () => {
    if (supplierMatchResults.length === 0) return;

    const exportData: any[] = [];
    supplierMatchResults.forEach(result => {
      result.matched_suppliers.forEach((supplier, idx) => {
        exportData.push({
          source_product: result.source_product_title,
          rank: idx + 1,
          supplier_title: supplier.title,
          price_cny: supplier.price,
          moq: supplier.moq,
          sold_count: supplier.sold_count,
          supplier_name: supplier.supplier_name,
          location: supplier.location || '',
          is_verified: supplier.is_verified ? 'Yes' : 'No',
          match_score: supplier.match_score?.toFixed(1) || '',
          product_url: supplier.product_url,
        });
      });
    });

    const csvContent = [
      Object.keys(exportData[0]).join(','),
      ...exportData.map(row => Object.values(row).map(v => `"${v}"`).join(','))
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `1688_suppliers_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const rowSelection: TableRowSelection<HotProduct> = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys, newSelectedRows) => {
      setSelectedRowKeys(newSelectedRowKeys);
      setSelectedProducts(newSelectedRows);
    },
  };

  const productColumns = [
    { title: t('products.product'), dataIndex: 'title', key: 'title', ellipsis: true },
    { title: t('products.platform'), dataIndex: 'platform', key: 'platform', render: (p: string) => <Tag color={platformColors[p] || 'default'}>{p.toUpperCase()}</Tag> },
    { title: t('products.price'), dataIndex: 'price', key: 'price', render: (price: number | string, record: Product) => price ? `${record.currency} ${Number(price).toFixed(2)}` : '-' },
    { title: t('products.rating'), dataIndex: 'rating', key: 'rating', render: (r: number) => r ? `${r.toFixed(1)}` : '-' },
  ];

  const hotProductColumns = [
    {
      title: t('products.image'),
      dataIndex: 'image_url',
      key: 'image',
      width: 70,
      render: (url: string) => url ? (
        <Image src={url} alt="Product" width={50} height={50} style={{ objectFit: 'cover', borderRadius: 4 }} fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
      ) : (
        <div style={{ width: 50, height: 50, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4 }}>
          <PictureOutlined style={{ color: '#bfbfbf', fontSize: 20 }} />
        </div>
      )
    },
    {
      title: t('products.product'),
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text: string, record: HotProduct) => (
        <a
          onClick={() => setSelectedProduct(record)}
          style={{ color: '#1890ff', cursor: 'pointer' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#40a9ff')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#1890ff')}
          title={text}
        >
          {text}
        </a>
      )
    },
    {
      title: t('products.platform'),
      dataIndex: 'platform',
      key: 'platform',
      width: 100,
      render: (p: string) => <Tag color={platformColors[p] || 'default'}>{p.toUpperCase()}</Tag>
    },
    {
      title: t('products.price'),
      dataIndex: 'price',
      key: 'price',
      width: 100,
      render: (price: number | string, record: Product) => price ? `${record.currency} ${Number(price).toFixed(2)}` : '-'
    },
    {
      title: t('products.salesData'),
      key: 'sales',
      width: 180,
      render: (_: any, record: Product & { hot_score: number }) => (
        <span style={{ fontSize: 12, color: '#666' }}>{getSalesDisplay(record)}</span>
      )
    },
    {
      title: t('dashboard.hotScore'),
      dataIndex: 'hot_score',
      key: 'hot_score',
      width: 80,
      render: (score: number) => <Tag color="red">{score.toFixed(0)}</Tag>
    },
    {
      title: t('products.actions'),
      key: 'actions',
      width: 120,
      render: (_: any, record: HotProduct) => (
        <Space size="small">
          <Tooltip title={t('products.viewDetails')}>
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => setSelectedProduct(record)}
            />
          </Tooltip>
          <Tooltip title={record.product_url ? t('dashboard.platformLink') : t('dashboard.noProductUrl')}>
            <Button
              type="text"
              size="small"
              icon={<LinkOutlined />}
              href={record.product_url}
              target="_blank"
              disabled={!record.product_url}
            />
          </Tooltip>
          <Tooltip title={t('dashboard.googleSearch')}>
            <Button
              type="text"
              size="small"
              icon={<SearchOutlined />}
              href={getGoogleShoppingUrl(record)}
              target="_blank"
            />
          </Tooltip>
        </Space>
      )
    },
  ];

  const getTrendChartOption = () => {
    if (!trendData?.data?.length) return {};
    const dates = trendData.data.map((d: any) => d.date);
    const values = trendData.data.map((d: any) => d[trendData.keywords?.[0]] || 0);
    return {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { rotate: 45 },
        name: t('trends.xAxisLabel'),
        nameLocation: 'middle',
        nameGap: 35
      },
      yAxis: {
        type: 'value',
        name: t('trends.yAxisLabel'),
        max: 100,
        nameLocation: 'middle',
        nameGap: 50,
        nameRotate: 90
      },
      series: [{ name: trendData.keywords?.[0] || 'Trend', type: 'line', data: values, smooth: true, areaStyle: { opacity: 0.3 } }],
      grid: { left: 80, right: 20, bottom: 60, top: 30 }
    };
  };

  const getTrendCardTitle = () => {
    if (selectedProductForTrend) {
      const shortTitle = selectedProductForTrend.length > 30 ? selectedProductForTrend.substring(0, 30) + '...' : selectedProductForTrend;
      return t('dashboard.googleTrendsFor', { product: shortTitle });
    }
    return t('dashboard.googleTrends');
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: 0 }}>{t('dashboard.title')}</h1>
        <Space>
          <Button type="primary" icon={<FireOutlined />} onClick={findHotProducts} loading={hotLoading} danger>
            {hotLoading ? t('dashboard.finding') : t('dashboard.findHotProducts')}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadDashboardData} loading={loading}>{t('dashboard.refresh')}</Button>
        </Space>
      </div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title={t('dashboard.totalProducts')} value={products.length} prefix={<ShoppingOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.reportsGenerated')} value={reports.length} prefix={<FileTextOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.platforms')} value={4} prefix={<GlobalOutlined />} /></Card></Col>
        <Col span={6}><Card><Statistic title={t('dashboard.trending')} value={t('dashboard.active')} prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} /></Card></Col>
      </Row>
      {hotProducts.length > 0 && (
        <Card title={<><FireOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />{t('dashboard.topHotProducts')}</>} style={{ marginBottom: 16 }}>
          <Table
            dataSource={hotProducts}
            columns={hotProductColumns}
            rowKey="id"
            pagination={false}
            size="small"
            scroll={{ x: 900 }}
            rowSelection={rowSelection}
          />
        </Card>
      )}
      <Row gutter={16}>
        <Col span={12}>
          <Card
            title={getTrendCardTitle()}
            extra={
              <Space>
                {hotProducts.length > 0 && (
                  <Select
                    style={{ width: 200 }}
                    placeholder={t('dashboard.selectProduct')}
                    allowClear
                    onChange={(value) => value && loadTrendForProduct(value)}
                    loading={trendLoading}
                    size="small"
                  >
                    {hotProducts.map((p) => (
                      <Select.Option key={p.id} value={p.title}>
                        {p.title.length > 30 ? p.title.substring(0, 30) + '...' : p.title}
                      </Select.Option>
                    ))}
                  </Select>
                )}
                <Tag color="blue">{t('dashboard.sample')}</Tag>
              </Space>
            }
          >
            {trendData?.data?.length ? (
              <>
                <ReactECharts option={getTrendChartOption()} style={{ height: 300 }} />
                <div style={{ marginTop: 8, padding: '8px 12px', background: '#f6f8fa', borderRadius: 4, fontSize: 12, color: '#666' }}>
                  {t('trends.chartExplanation')}
                </div>
              </>
            ) : (
              <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{t('dashboard.noTrendData')}</div>
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title={t('dashboard.recentReports')} extra={<Button type="link" onClick={() => navigate('/reports')}>{t('dashboard.viewAll')}</Button>}>
            {reports.length > 0 ? (
              <Table dataSource={reports} rowKey="id" pagination={false} size="small" columns={[
                { title: t('reports.title'), dataIndex: 'title', key: 'title', ellipsis: true },
                { title: t('reports.status'), dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : 'blue'}>{s}</Tag> },
                { title: t('reports.score'), dataIndex: 'overall_score', key: 'score', render: (s: number) => s ? `${s}/100` : '-' },
              ]} />
            ) : <div style={{ textAlign: 'center', padding: 40 }}>{t('dashboard.noReports')}</div>}
          </Card>
        </Col>
      </Row>
      <Card title={t('dashboard.recentProducts')} style={{ marginTop: 16, marginBottom: selectedProducts.length > 0 ? 180 : 0 }}>
        <Table dataSource={products} columns={productColumns} rowKey="id" pagination={false} loading={loading} />
      </Card>

      {/* Product Details Modal */}
      <Modal
        title={t('products.productDetails')}
        open={!!selectedProduct}
        onCancel={() => setSelectedProduct(null)}
        width={800}
        footer={[
          selectedProduct?.product_url && (
            <Button key="platform" icon={<LinkOutlined />} href={selectedProduct.product_url} target="_blank">
              {t('dashboard.platformLink')}
            </Button>
          ),
          <Button key="google" icon={<SearchOutlined />} href={selectedProduct ? getGoogleShoppingUrl(selectedProduct) : ''} target="_blank">
            {t('dashboard.googleSearch')}
          </Button>,
          <Button key="report" type="primary" icon={<FileAddOutlined />} onClick={() => { if (selectedProduct) handleGenerateReport(selectedProduct); setSelectedProduct(null); }}>
            {t('products.generateReport')}
          </Button>,
          <Button key="close" onClick={() => setSelectedProduct(null)}>
            {t('products.close')}
          </Button>,
        ].filter(Boolean)}
      >
        {selectedProduct && (
          <>
            <Row gutter={24}>
              <Col span={8}>
                {selectedProduct.image_url ? (
                  <Image src={selectedProduct.image_url} alt="Product" style={{ width: '100%', borderRadius: 8 }} />
                ) : (
                  <div style={{ width: '100%', height: 200, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 8 }}>
                    <PictureOutlined style={{ fontSize: 48, color: '#bfbfbf' }} />
                  </div>
                )}
              </Col>
              <Col span={16}>
                <Descriptions bordered column={2} size="small">
                  <Descriptions.Item label={t('products.product')} span={2}>{selectedProduct.title}</Descriptions.Item>
                  <Descriptions.Item label={t('products.platform')}>
                    <Tag color={platformColors[selectedProduct.platform]}>{selectedProduct.platform.toUpperCase()}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label={t('products.price')}>
                    {selectedProduct.price ? `${selectedProduct.currency} ${Number(selectedProduct.price).toFixed(2)}` : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label={t('products.rating')}>
                    {selectedProduct.rating ? Number(selectedProduct.rating).toFixed(1) : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label={t('products.reviews')}>
                    {selectedProduct.review_count || 0}
                  </Descriptions.Item>
                  <Descriptions.Item label={t('dashboard.hotScore')}>
                    <Tag color="red">{selectedProduct.hot_score?.toFixed(0) || '-'}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label={t('products.salesData')}>
                    {getSalesDisplay(selectedProduct)}
                  </Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>
          </>
        )}
      </Modal>

      {/* Selected Products Floating Panel */}
      {selectedProducts.length > 0 && (
        <div
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#fff',
            borderTop: '2px solid #1890ff',
            boxShadow: '0 -4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            padding: selectionPanelCollapsed ? '12px 24px' : '16px 24px',
            transition: 'all 0.3s ease',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: selectionPanelCollapsed ? 0 : 12 }}>
            <Space>
              <ShoppingOutlined style={{ color: '#1890ff', fontSize: 18 }} />
              <span style={{ fontWeight: 'bold', fontSize: 16 }}>
                {t('dashboard.selectedProducts')} ({selectedProducts.length})
              </span>
            </Space>
            <Space>
              <Button size="small" onClick={handleClearAllSelections} icon={<DeleteOutlined />}>
                {t('dashboard.clearAll')}
              </Button>
              <Button
                size="small"
                type="text"
                icon={selectionPanelCollapsed ? <UpOutlined /> : <DownOutlined />}
                onClick={() => setSelectionPanelCollapsed(!selectionPanelCollapsed)}
              >
                {selectionPanelCollapsed ? t('dashboard.expand') : t('dashboard.collapse')}
              </Button>
              <Button size="small" type="text" icon={<CloseOutlined />} onClick={handleClearAllSelections} />
            </Space>
          </div>

          {!selectionPanelCollapsed && (
            <>
              <div style={{ overflowX: 'auto', whiteSpace: 'nowrap', paddingBottom: 12 }}>
                <Row gutter={12} style={{ flexWrap: 'nowrap', display: 'inline-flex' }}>
                  {selectedProducts.map(product => (
                    <Col key={product.id} style={{ width: 180, flex: '0 0 180px' }}>
                      <Card
                        size="small"
                        style={{ height: '100%' }}
                        cover={
                          product.image_url ? (
                            <div style={{ height: 80, overflow: 'hidden' }}>
                              <img src={product.image_url} alt={product.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                            </div>
                          ) : (
                            <div style={{ height: 80, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <PictureOutlined style={{ color: '#bfbfbf', fontSize: 24 }} />
                            </div>
                          )
                        }
                      >
                        <div style={{ fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={product.title}>
                          {product.title}
                        </div>
                        <div style={{ fontSize: 14, color: '#1890ff', fontWeight: 'bold', marginTop: 4 }}>
                          {product.currency} {Number(product.price).toFixed(2)}
                        </div>
                        <Button
                          size="small"
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleRemoveFromSelection(product.id)}
                          style={{ marginTop: 4, padding: 0 }}
                        >
                          {t('dashboard.removeFromSelection')}
                        </Button>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </div>

              <Divider style={{ margin: '8px 0' }} />

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Space>
                  <Button icon={<ExportOutlined />} onClick={handleExportSelected}>
                    {t('dashboard.exportSelected')}
                  </Button>
                  <Button
                    type="primary"
                    icon={<ShopOutlined />}
                    onClick={handleMatch1688Suppliers}
                    style={{ background: '#ff6600', borderColor: '#ff6600' }}
                  >
                    {t('suppliers.match1688')}
                  </Button>
                  <Button type="primary" icon={<FileAddOutlined />} onClick={handleGenerateComparisonReport} disabled={selectedProducts.length < 2}>
                    {t('dashboard.generateComparisonReport')}
                  </Button>
                </Space>
              </div>
            </>
          )}
        </div>
      )}

      {/* 1688 Supplier Match Drawer */}
      <Drawer
        title={
          <Space>
            <ShopOutlined style={{ color: '#ff6600' }} />
            {t('suppliers.matchResults')}
          </Space>
        }
        placement="right"
        width={900}
        open={supplierDrawerVisible}
        onClose={() => setSupplierDrawerVisible(false)}
        extra={
          <Space>
            <Button icon={<ExportOutlined />} onClick={exportSupplierResults} disabled={supplierMatchResults.length === 0}>
              {t('suppliers.exportPurchaseList')}
            </Button>
          </Space>
        }
      >
        {/* Match Settings */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16} align="middle">
            <Col span={6}>
              <div style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>{t('suppliers.maxPriceLabel')} (CNY)</div>
              <Slider
                min={100}
                max={1000}
                step={50}
                value={supplierMaxPrice}
                onChange={setSupplierMaxPrice}
                marks={{ 100: '100', 500: '500', 1000: '1000' }}
              />
            </Col>
            <Col span={4}>
              <div style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>{t('suppliers.limitLabel')}</div>
              <InputNumber
                min={5}
                max={20}
                value={supplierLimit}
                onChange={(v) => setSupplierLimit(v || 10)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>{t('suppliers.includeLargeItems')}</div>
              <Switch checked={includeLargeItems} onChange={setIncludeLargeItems} />
            </Col>
            <Col span={8} style={{ textAlign: 'right' }}>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={handleMatch1688Suppliers}
                loading={supplierLoading}
                style={{ background: '#ff6600', borderColor: '#ff6600' }}
              >
                {supplierLoading ? t('suppliers.matching') : t('suppliers.startMatching')}
              </Button>
            </Col>
          </Row>
        </Card>

        {/* Loading State */}
        {supplierLoading && (
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#666' }}>{t('suppliers.matching')}</div>
          </div>
        )}

        {/* Match Results */}
        {!supplierLoading && supplierMatchResults.length > 0 && (
          <div>
            {supplierMatchResults.map((result, resultIdx) => {
              const sourceProduct = getSourceProductForSupplier(result.source_product_id);
              return (
                <Card
                  key={result.source_product_id}
                  title={
                    <Space>
                      <Tag color="blue">{resultIdx + 1}</Tag>
                      <span style={{ fontWeight: 500 }}>{result.source_product_title.substring(0, 50)}...</span>
                      <Tag color="green">{sourceProduct?.currency} {Number(sourceProduct?.price).toFixed(2)}</Tag>
                    </Space>
                  }
                  size="small"
                  style={{ marginBottom: 16 }}
                  extra={
                    <Space size="small">
                      <span style={{ fontSize: 12, color: '#666' }}>
                        {t('suppliers.searchKeywords')}: {result.search_keywords.join(', ')}
                      </span>
                      <Tag>{result.match_count} {t('suppliers.topSuppliers', { count: result.match_count })}</Tag>
                    </Space>
                  }
                >
                  {result.matched_suppliers.length === 0 ? (
                    <Alert
                      message={t('suppliers.noSuppliers')}
                      description={t('suppliers.tryAnotherKeyword')}
                      type="warning"
                      showIcon
                    />
                  ) : (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                      {result.matched_suppliers.map((supplier, idx) => (
                        <Card
                          key={supplier.offer_id}
                          size="small"
                          style={{ marginBottom: 8 }}
                          hoverable
                        >
                          <Row gutter={16} align="middle">
                            <Col span={2}>
                              <Tag color={idx < 3 ? 'gold' : 'default'} style={{ fontSize: 14 }}>
                                #{idx + 1}
                              </Tag>
                            </Col>
                            <Col span={3}>
                              {supplier.image_url ? (
                                <Image
                                  src={supplier.image_url}
                                  width={60}
                                  height={60}
                                  style={{ objectFit: 'cover', borderRadius: 4 }}
                                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                                />
                              ) : (
                                <div style={{ width: 60, height: 60, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4 }}>
                                  <PictureOutlined style={{ color: '#bfbfbf', fontSize: 24 }} />
                                </div>
                              )}
                            </Col>
                            <Col span={9}>
                              <div style={{ fontWeight: 500, marginBottom: 4 }}>
                                {supplier.title.substring(0, 40)}...
                              </div>
                              <Space size="small" wrap>
                                <Tag color="red" style={{ fontWeight: 'bold' }}>
                                  {supplier.price_range || `\u00A5${supplier.price}`}
                                </Tag>
                                <Tag>{t('suppliers.moq')}: {supplier.moq}</Tag>
                                <Tag color="green">{t('suppliers.soldCount')}: {supplier.sold_count}</Tag>
                              </Space>
                            </Col>
                            <Col span={5}>
                              <div style={{ fontSize: 12 }}>
                                <div style={{ marginBottom: 4 }}>
                                  <ShopOutlined style={{ marginRight: 4 }} />
                                  {supplier.supplier_name.substring(0, 15)}
                                  {supplier.is_verified && (
                                    <Tag color="gold" style={{ marginLeft: 4 }} size="small">
                                      <SafetyCertificateOutlined /> {t('suppliers.verified')}
                                    </Tag>
                                  )}
                                </div>
                                {supplier.location && (
                                  <div style={{ color: '#666' }}>
                                    <EnvironmentOutlined style={{ marginRight: 4 }} />
                                    {supplier.location}
                                  </div>
                                )}
                                {supplier.supplier_rating && (
                                  <Rate disabled defaultValue={supplier.supplier_rating} style={{ fontSize: 12 }} />
                                )}
                              </div>
                            </Col>
                            <Col span={5} style={{ textAlign: 'right' }}>
                              <div style={{ marginBottom: 8 }}>
                                <Tag color="blue">{t('suppliers.matchScore')}: {supplier.match_score?.toFixed(0)}</Tag>
                              </div>
                              <Space size="small">
                                <Tooltip title={t('suppliers.calculateProfit')}>
                                  <Button
                                    size="small"
                                    icon={<CalculatorOutlined />}
                                    onClick={() => {
                                      setSelectedSupplier(supplier);
                                      setProfitModalVisible(true);
                                    }}
                                  />
                                </Tooltip>
                                <Tooltip title={t('suppliers.visit1688')}>
                                  <Button
                                    size="small"
                                    type="primary"
                                    icon={<LinkOutlined />}
                                    href={supplier.product_url}
                                    target="_blank"
                                    style={{ background: '#ff6600', borderColor: '#ff6600' }}
                                  />
                                </Tooltip>
                              </Space>
                            </Col>
                          </Row>
                        </Card>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        )}

        {/* No Results */}
        {!supplierLoading && supplierMatchResults.length === 0 && (
          <div style={{ textAlign: 'center', padding: 60, color: '#666' }}>
            <ShopOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <div>{t('suppliers.noMatch')}</div>
          </div>
        )}
      </Drawer>

      {/* Profit Calculator Modal */}
      <Modal
        title={
          <Space>
            <CalculatorOutlined />
            {t('suppliers.profitCalculator')}
          </Space>
        }
        open={profitModalVisible}
        onCancel={() => setProfitModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setProfitModalVisible(false)}>
            {t('suppliers.close')}
          </Button>
        ]}
        width={600}
      >
        {selectedSupplier && (() => {
          // Find the source product for this supplier
          const matchResult = supplierMatchResults.find(r =>
            r.matched_suppliers.some(s => s.offer_id === selectedSupplier.offer_id)
          );
          const sourceProduct = matchResult ? getSourceProductForSupplier(matchResult.source_product_id) : null;

          if (!sourceProduct) return <div>Source product not found</div>;

          const profitData = calculateEstimatedProfit(selectedSupplier, sourceProduct);

          return (
            <>
              <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label={t('suppliers.sourceProduct')}>
                  {sourceProduct.title.substring(0, 50)}...
                  <Tag color="blue" style={{ marginLeft: 8 }}>
                    {sourceProduct.currency} {Number(sourceProduct.price).toFixed(2)}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label={t('suppliers.supplierInfo')}>
                  {selectedSupplier.supplier_name}
                  <Tag color="red" style={{ marginLeft: 8 }}>
                    \u00A5{selectedSupplier.price}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>

              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8 }}>{t('suppliers.quantity')}</div>
                <InputNumber
                  min={selectedSupplier.moq}
                  value={profitQuantity}
                  onChange={(v) => setProfitQuantity(v || 100)}
                  style={{ width: 200 }}
                  addonAfter="pcs"
                />
                <span style={{ marginLeft: 8, color: '#666', fontSize: 12 }}>
                  {t('suppliers.moq')}: {selectedSupplier.moq}
                </span>
              </div>

              <Row gutter={16}>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title={t('suppliers.purchaseCost') + ' (CNY)'}
                      value={selectedSupplier.price * profitQuantity}
                      precision={2}
                      prefix="\u00A5"
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <Statistic
                      title={t('suppliers.shippingCost') + ' (CNY)'}
                      value={15 * profitQuantity}
                      precision={2}
                      prefix="\u00A5"
                    />
                  </Card>
                </Col>
              </Row>

              <Divider />

              <Row gutter={16}>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title={t('suppliers.totalCost') + ` (${sourceProduct.currency})`}
                      value={profitData.totalCostTarget}
                      precision={2}
                      prefix={sourceProduct.currency === 'NZD' ? 'NZ$' : 'A$'}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title={t('suppliers.grossProfit')}
                      value={profitData.grossProfit}
                      precision={2}
                      prefix={sourceProduct.currency === 'NZD' ? 'NZ$' : 'A$'}
                      valueStyle={{ color: Number(profitData.grossProfit) > 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title={t('suppliers.profitMargin')}
                      value={profitData.profitMargin}
                      precision={1}
                      suffix="%"
                      valueStyle={{ color: Number(profitData.profitMargin) > 30 ? '#3f8600' : Number(profitData.profitMargin) > 15 ? '#faad14' : '#cf1322' }}
                    />
                  </Card>
                </Col>
              </Row>

              <div style={{ marginTop: 16, padding: 12, background: '#f6f8fa', borderRadius: 4 }}>
                <div style={{ fontSize: 12, color: '#666' }}>
                  <strong>{t('suppliers.notes')}:</strong>
                  <ul style={{ margin: '8px 0 0 20px', padding: 0 }}>
                    <li>{t('suppliers.exchangeRate')}: 1 {sourceProduct.currency} = {sourceProduct.currency === 'NZD' ? '4.30' : '4.70'} CNY</li>
                    <li>{t('suppliers.shippingCost')}: ~15 CNY/unit (estimated)</li>
                    <li>Platform fees (~15%) not included</li>
                    <li>Actual costs may vary</li>
                  </ul>
                </div>
              </div>
            </>
          );
        })()}
      </Modal>
    </div>
  );
};

export default Dashboard;
