import { useState } from 'react';
import { Card, Input, Select, Button, Table, Tag, Space, Row, Col, message, Modal, Descriptions, Image } from 'antd';
import { SearchOutlined, DownloadOutlined, EyeOutlined, FileAddOutlined } from '@ant-design/icons';
import { productsApi, reportsApi } from '../services/api';
import type { Product, ProductSearchParams } from '../types';

const { Search } = Input;
const { Option } = Select;

const Products = () => {
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
    if (!searchParams.keyword) { message.warning('Please enter a search keyword'); return; }
    setLoading(true);
    try {
      const data = await productsApi.search(searchParams);
      setProducts(data);
      if (data.length === 0) message.info('No products found. Try fetching from platforms.');
    } catch (error) { message.error('Search failed'); }
    finally { setLoading(false); }
  };

  const handleFetchFromPlatform = async (platform: string) => {
    if (!searchParams.keyword) { message.warning('Please enter a search keyword first'); return; }
    setFetchLoading(true);
    try {
      const result = await productsApi.fetchFromPlatform(searchParams.keyword, platform, 50);
      message.success(result.message);
      await handleSearch();
    } catch (error) { message.error('Failed to fetch from ' + platform); }
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
      message.success('Report generation started! Check Reports page.');
    } catch (error) { message.error('Failed to start report generation'); }
  };

  const columns = [
    { title: 'Image', dataIndex: 'image_url', key: 'image', width: 80,
      render: (url: string) => <Image src={url} alt="Product" width={60} height={60} style={{ objectFit: 'cover' }} /> },
    { title: 'Product', dataIndex: 'title', key: 'title', ellipsis: true,
      render: (text: string, record: Product) => <a onClick={() => setSelectedProduct(record)}>{text}</a> },
    { title: 'Platform', dataIndex: 'platform', key: 'platform', width: 100,
      render: (platform: string) => <Tag color={platformColors[platform] || 'default'}>{platform.replace('_', ' ').toUpperCase()}</Tag> },
    { title: 'Price', dataIndex: 'price', key: 'price', width: 100,
      render: (price: number | string, record: Product) => price ? record.currency + ' ' + Number(price).toFixed(2) : '-' },
    { title: 'Rating', dataIndex: 'rating', key: 'rating', width: 80,
      render: (rating: number | string) => rating ? '⭐ ' + Number(rating).toFixed(1) : '-' },
    { title: 'Reviews', dataIndex: 'review_count', key: 'reviews', width: 80 },
    { title: 'Actions', key: 'actions', width: 150,
      render: (_: any, record: Product) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setSelectedProduct(record)} />
          <Button size="small" icon={<FileAddOutlined />} onClick={() => handleGenerateReport(record)} title="Generate Report" />
          {record.product_url && <Button size="small" icon={<DownloadOutlined />} href={record.product_url} target="_blank" />}
        </Space>
      ) },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h1>Product Search</h1>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Search placeholder="Search products..." value={searchParams.keyword}
              onChange={(e) => setSearchParams({ ...searchParams, keyword: e.target.value })}
              onSearch={handleSearch} enterButton={<SearchOutlined />} size="large" />
          </Col>
          <Col span={4}>
            <Select style={{ width: '100%' }} placeholder="Platform" allowClear size="large"
              value={searchParams.platform} onChange={(value) => setSearchParams({ ...searchParams, platform: value })}>
              <Option value="ebay_au">eBay AU</Option>
              <Option value="ebay_nz">eBay NZ</Option>
              <Option value="amazon_au">Amazon AU</Option>
              <Option value="trademe">TradeMe</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select style={{ width: '100%' }} placeholder="Sort by" size="large"
              value={searchParams.sort_by} onChange={(value) => setSearchParams({ ...searchParams, sort_by: value })}>
              <Option value="relevance">Relevance</Option>
              <Option value="price_asc">Price: Low to High</Option>
              <Option value="price_desc">Price: High to Low</Option>
              <Option value="rating">Rating</Option>
              <Option value="reviews">Reviews</Option>
            </Select>
          </Col>
          <Col span={8}>
            <Space>
              <Button onClick={handleSearch} type="primary" loading={loading}>Search Database</Button>
              <Button onClick={() => handleFetchFromPlatform('ebay_au')} loading={fetchLoading}>Fetch eBay AU</Button>
              <Button onClick={() => handleFetchFromPlatform('ebay_nz')} loading={fetchLoading}>Fetch eBay NZ</Button>
            </Space>
          </Col>
        </Row>
      </Card>
      <Card title={'Results (' + products.length + ')'}>
        <Table dataSource={products} columns={columns} rowKey="id" loading={loading}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => 'Total ' + total + ' products' }} />
      </Card>
      <Modal title="Product Details" open={!!selectedProduct} onCancel={() => setSelectedProduct(null)} width={700}
        footer={[
          <Button key="close" onClick={() => setSelectedProduct(null)}>Close</Button>,
          <Button key="report" type="primary" onClick={() => { if (selectedProduct) handleGenerateReport(selectedProduct); setSelectedProduct(null); }}>Generate Report</Button>,
        ]}>
        {selectedProduct && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="Title" span={2}>{selectedProduct.title}</Descriptions.Item>
            <Descriptions.Item label="Platform"><Tag color={platformColors[selectedProduct.platform]}>{selectedProduct.platform.toUpperCase()}</Tag></Descriptions.Item>
            <Descriptions.Item label="Price">{selectedProduct.price ? selectedProduct.currency + ' ' + Number(selectedProduct.price).toFixed(2) : '-'}</Descriptions.Item>
            <Descriptions.Item label="Rating">{selectedProduct.rating ? '⭐ ' + Number(selectedProduct.rating).toFixed(1) : '-'}</Descriptions.Item>
            <Descriptions.Item label="Reviews">{selectedProduct.review_count}</Descriptions.Item>
            <Descriptions.Item label="Category" span={2}>{selectedProduct.category || '-'}</Descriptions.Item>
            <Descriptions.Item label="Link" span={2}>{selectedProduct.product_url ? <a href={selectedProduct.product_url} target="_blank" rel="noreferrer">View on Platform</a> : '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default Products;
