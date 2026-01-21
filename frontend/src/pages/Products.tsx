import { useState } from 'react';
import { Card, Input, Select, Button, Table, Tag, Space, Row, Col, message, Modal, Descriptions, Image, Divider } from 'antd';
import { SearchOutlined, DownloadOutlined, EyeOutlined, FileAddOutlined, PictureOutlined, ShopOutlined, TrophyOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { productsApi, reportsApi } from '../services/api';
import type { Product, ProductSearchParams } from '../types';

const { Search } = Input;
const { Option } = Select;

const Products = () => {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchParams, setSearchParams] = useState<ProductSearchParams>({
    keyword: '',
    platform: undefined,
    sort_by: 'relevance',
    page: 1,
    page_size: 20,
  });

  const platformColors: Record<string, string> = {
    ebay_au: 'blue', ebay_nz: 'green', amazon_au: 'orange', trademe: 'purple',
  };

  const handleSearch = async () => {
    if (!searchParams.keyword) { message.warning(t('products.enterKeyword')); return; }
    setLoading(true);
    try {
      const data = await productsApi.search(searchParams);
      setProducts(data);
      if (data.length === 0) message.info(t('products.noProducts'));
    } catch (error) { message.error(t('products.searchFailed')); }
    finally { setLoading(false); }
  };

  const handleFetchFromPlatform = async (platform: string) => {
    if (!searchParams.keyword) { message.warning(t('products.enterKeyword')); return; }
    setFetchLoading(true);
    try {
      const result = await productsApi.fetchFromPlatform(searchParams.keyword, platform, 50);
      message.success(result.message);
      await handleSearch();
    } catch (error) { message.error(t('products.fetchFailed') + platform); }
    finally { setFetchLoading(false); }
  };

  const handleGenerateReport = async (product: Product) => {
    try {
      await reportsApi.generate({
        title: 'Report: ' + product.title.substring(0, 50),
        report_type: 'quick',
        target_type: 'product',
        target_value: product.id,
      });
      message.success(t('products.reportStarted'));
    } catch (error) { message.error(t('products.reportFailed')); }
  };

  const getSalesDisplay = (product: Product) => {
    const monthlySalesEst = product.review_count ? product.review_count * 25 : 0;
    if (product.sold_count) {
      return (
        <span>
          <span style={{ color: '#52c41a' }}>{t('products.soldCount')}: {product.sold_count}</span>
          <br />
          <span style={{ color: '#666', fontSize: 11 }}>{t('products.monthlySalesEst')}: ~{monthlySalesEst}</span>
        </span>
      );
    }
    return monthlySalesEst > 0 ? (
      <span style={{ color: '#666', fontSize: 12 }}>{t('products.monthlySalesEst')}: ~{monthlySalesEst}</span>
    ) : '-';
  };

  const columns = [
    { title: t('products.image'), dataIndex: 'image_url', key: 'image', width: 80,
      render: (url: string) => url ? (
        <Image src={url} alt="Product" width={60} height={60} style={{ objectFit: 'cover' }} fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" />
      ) : (
        <div style={{ width: 60, height: 60, background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <PictureOutlined style={{ color: '#bfbfbf', fontSize: 24 }} />
        </div>
      )
    },
    { title: t('products.product'), dataIndex: 'title', key: 'title', ellipsis: true,
      render: (text: string, record: Product) => <a onClick={() => setSelectedProduct(record)}>{text}</a> },
    { title: t('products.platform'), dataIndex: 'platform', key: 'platform', width: 100,
      render: (platform: string) => <Tag color={platformColors[platform] || 'default'}>{platform.replace('_', ' ').toUpperCase()}</Tag> },
    { title: t('products.price'), dataIndex: 'price', key: 'price', width: 100,
      render: (price: number | string, record: Product) => price ? record.currency + ' ' + Number(price).toFixed(2) : '-' },
    { title: t('products.bsrRank'), dataIndex: 'bsr_rank', key: 'bsr_rank', width: 90,
      render: (rank: number) => rank ? <Tag color="gold"><TrophyOutlined /> #{rank}</Tag> : '-' },
    { title: t('products.sellerCount'), dataIndex: 'seller_count', key: 'seller_count', width: 80,
      render: (count: number) => count ? <span><ShopOutlined style={{ marginRight: 4 }} />{count}</span> : '-' },
    { title: t('products.salesData'), key: 'sales', width: 130,
      render: (_: any, record: Product) => getSalesDisplay(record) },
    { title: t('products.rating'), dataIndex: 'rating', key: 'rating', width: 80,
      render: (rating: number | string) => rating ? Number(rating).toFixed(1) : '-' },
    { title: t('products.reviews'), dataIndex: 'review_count', key: 'reviews', width: 80 },
    { title: t('products.actions'), key: 'actions', width: 150,
      render: (_: any, record: Product) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setSelectedProduct(record)} />
          <Button size="small" icon={<FileAddOutlined />} onClick={() => handleGenerateReport(record)} title={t('products.generateReport')} />
          {record.product_url && <Button size="small" icon={<DownloadOutlined />} href={record.product_url} target="_blank" />}
        </Space>
      ) },
  ];

  const renderPlatformComparisonCard = (product: Product) => {
    const platforms = [
      { key: 'ebay_au', name: 'eBay AU', color: '#1890ff' },
      { key: 'ebay_nz', name: 'eBay NZ', color: '#52c41a' },
      { key: 'amazon_au', name: 'Amazon AU', color: '#fa8c16' },
      { key: 'trademe', name: 'TradeMe', color: '#722ed1' },
    ];

    const currentPlatform = platforms.find(p => p.key === product.platform);

    return (
      <Card
        size="small"
        title={<><ShopOutlined style={{ marginRight: 8 }} />{t('products.platformComparison')}</>}
        style={{ marginTop: 16 }}
      >
        <Row gutter={16}>
          {platforms.map(platform => {
            const isCurrent = platform.key === product.platform;
            return (
              <Col span={6} key={platform.key}>
                <div style={{
                  padding: 12,
                  border: `2px solid ${isCurrent ? platform.color : '#f0f0f0'}`,
                  borderRadius: 8,
                  background: isCurrent ? `${platform.color}10` : '#fafafa',
                  textAlign: 'center'
                }}>
                  <div style={{
                    fontWeight: 'bold',
                    color: platform.color,
                    marginBottom: 8
                  }}>
                    {platform.name}
                  </div>
                  {isCurrent ? (
                    <>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        <TrophyOutlined /> {t('products.bsrRank')}: {product.bsr_rank || '-'}
                      </div>
                      <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                        <ShopOutlined /> {t('products.sellerCount')}: {product.seller_count || '-'}
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: 12, color: '#999' }}>
                      {t('trends.noData')}
                    </div>
                  )}
                </div>
              </Col>
            );
          })}
        </Row>
      </Card>
    );
  };

  const renderSalesDataCard = (product: Product) => {
    const monthlySalesEst = product.review_count ? product.review_count * 25 : 0;

    return (
      <Card
        size="small"
        title={<><TrophyOutlined style={{ marginRight: 8 }} />{t('products.salesData')}</>}
        style={{ marginTop: 16 }}
      >
        <Row gutter={24}>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                {product.sold_count || '-'}
              </div>
              <div style={{ fontSize: 12, color: '#666' }}>{t('products.soldCount')}</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                ~{monthlySalesEst || '-'}
              </div>
              <div style={{ fontSize: 12, color: '#666' }}>{t('products.monthlySalesEst')}</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#fa8c16' }}>
                {product.review_count || 0}
              </div>
              <div style={{ fontSize: 12, color: '#666' }}>{t('products.reviews')}</div>
            </div>
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>{t('products.title')}</h1>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Search placeholder={t('products.searchPlaceholder')} value={searchParams.keyword}
              onChange={(e) => setSearchParams({ ...searchParams, keyword: e.target.value })}
              onSearch={handleSearch} enterButton={<SearchOutlined />} size="large" />
          </Col>
          <Col span={4}>
            <Select style={{ width: '100%' }} placeholder={t('products.platform')} allowClear size="large"
              value={searchParams.platform} onChange={(value) => setSearchParams({ ...searchParams, platform: value })}>
              <Option value="ebay_au">{t('platforms.ebay_au')}</Option>
              <Option value="ebay_nz">{t('platforms.ebay_nz')}</Option>
              <Option value="amazon_au">{t('platforms.amazon_au')}</Option>
              <Option value="trademe">{t('platforms.trademe')}</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select style={{ width: '100%' }} placeholder={t('products.sortBy')} size="large"
              value={searchParams.sort_by} onChange={(value) => setSearchParams({ ...searchParams, sort_by: value })}>
              <Option value="relevance">{t('products.relevance')}</Option>
              <Option value="price_asc">{t('products.priceLowHigh')}</Option>
              <Option value="price_desc">{t('products.priceHighLow')}</Option>
              <Option value="rating">{t('products.rating')}</Option>
              <Option value="reviews">{t('products.reviews')}</Option>
            </Select>
          </Col>
          <Col span={8}>
            <Space>
              <Button onClick={handleSearch} type="primary" loading={loading}>{t('products.searchDatabase')}</Button>
              <Button onClick={() => handleFetchFromPlatform('ebay_au')} loading={fetchLoading}>{t('products.fetchEbayAU')}</Button>
              <Button onClick={() => handleFetchFromPlatform('ebay_nz')} loading={fetchLoading}>{t('products.fetchEbayNZ')}</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      <Card title={t('products.results') + ' (' + products.length + ')'}>
        <Table dataSource={products} columns={columns} rowKey="id" loading={loading} scroll={{ x: 1200 }}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => t('products.totalProducts', { count: total }) }} />
      </Card>
      <Modal title={t('products.productDetails')} open={!!selectedProduct} onCancel={() => setSelectedProduct(null)} width={800}
        footer={[
          <Button key="close" onClick={() => setSelectedProduct(null)}>{t('products.close')}</Button>,
          <Button key="report" type="primary" onClick={() => { if (selectedProduct) handleGenerateReport(selectedProduct); setSelectedProduct(null); }}>{t('products.generateReport')}</Button>,
        ]}>
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
                  <Descriptions.Item label={t('products.platform')}><Tag color={platformColors[selectedProduct.platform]}>{selectedProduct.platform.toUpperCase()}</Tag></Descriptions.Item>
                  <Descriptions.Item label={t('products.price')}>{selectedProduct.price ? selectedProduct.currency + ' ' + Number(selectedProduct.price).toFixed(2) : '-'}</Descriptions.Item>
                  <Descriptions.Item label={t('products.bsrRank')}>{selectedProduct.bsr_rank ? <Tag color="gold">#{selectedProduct.bsr_rank}</Tag> : '-'}</Descriptions.Item>
                  <Descriptions.Item label={t('products.sellerCount')}>{selectedProduct.seller_count || '-'}</Descriptions.Item>
                  <Descriptions.Item label={t('products.rating')}>{selectedProduct.rating ? Number(selectedProduct.rating).toFixed(1) : '-'}</Descriptions.Item>
                  <Descriptions.Item label={t('products.reviews')}>{selectedProduct.review_count}</Descriptions.Item>
                  <Descriptions.Item label={t('products.category')} span={2}>{selectedProduct.category || '-'}</Descriptions.Item>
                  <Descriptions.Item label={t('products.link')} span={2}>{selectedProduct.product_url ? <a href={selectedProduct.product_url} target="_blank" rel="noreferrer">{t('products.viewOnPlatform')}</a> : '-'}</Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>

            {renderSalesDataCard(selectedProduct)}
            {renderPlatformComparisonCard(selectedProduct)}
          </>
        )}
      </Modal>
    </div>
  );
};

export default Products;
