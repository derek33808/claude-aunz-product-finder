import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Input, Select, Image, Statistic, Space, Button, Typography, message, Collapse, Badge } from 'antd';
import { ShopOutlined, SearchOutlined, ReloadOutlined, DollarOutlined, LinkOutlined, TrophyOutlined, FireOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { supabase } from '../services/supabase';

const { Title, Text } = Typography;
const { Search } = Input;

// TOP 10 推荐选品数据
const TOP10_PRODUCTS = [
  { rank: 1, title: '八爪鱼太阳能庭院灯(防水遥控)', category: '庭院监控', price: 22, auPriceLow: 14, auPriceHigh: 23, profitRate: '200%+', url: 'https://detail.1688.com/offer/902544931709.html' },
  { rank: 2, title: '头戴式蓝牙耳机(降噪长续航)', category: '蓝牙耳机', price: 35, auPriceLow: 22, auPriceHigh: 37, profitRate: '200%+', url: 'https://detail.1688.com/offer/878346774131.html' },
  { rank: 3, title: '20000mAh充电宝(自带线数显)', category: '充电宝', price: 11, auPriceLow: 7, auPriceHigh: 15, profitRate: '200%+', url: 'https://detail.1688.com/offer/902558239373.html' },
  { rank: 4, title: '迷你充电宝(四线便携)', category: '充电宝', price: 16, auPriceLow: 10, auPriceHigh: 17, profitRate: '200%+', url: 'https://detail.1688.com/offer/943461513723.html' },
  { rank: 5, title: 'TPE双色瑜伽垫(6mm防滑)', category: '瑜伽垫', price: 15, auPriceLow: 9, auPriceHigh: 16, profitRate: '180%+', url: 'https://detail.1688.com/offer/604191338681.html' },
  { rank: 6, title: 'TWS蓝牙耳机(游戏触控)', category: '蓝牙耳机', price: 15, auPriceLow: 9, auPriceHigh: 16, profitRate: '180%+', url: 'https://detail.1688.com/offer/1007496887108.html' },
  { rank: 7, title: 'AI翻译蓝牙耳机(开放式)', category: '蓝牙耳机', price: 40, auPriceLow: 25, auPriceHigh: 42, profitRate: '200%+', url: 'https://detail.1688.com/offer/986395632592.html' },
  { rank: 8, title: 'ANC降噪蓝牙耳机(苹果适用)', category: '蓝牙耳机', price: 38, auPriceLow: 24, auPriceHigh: 40, profitRate: '200%+', url: 'https://detail.1688.com/offer/918394204383.html' },
  { rank: 9, title: '运动骑行太阳镜(防紫外线)', category: '太阳镜', price: 3, auPriceLow: 5, auPriceHigh: 10, profitRate: '300%+', url: 'https://detail.1688.com/offer/649724946654.html' },
  { rank: 10, title: '户外折叠野餐桌(便携轻量)', category: '野餐桌', price: 18, auPriceLow: 12, auPriceHigh: 20, profitRate: '200%+', url: 'https://detail.1688.com/offer/5926100527361.html' },
];

interface Supplier1688 {
  id: string;
  title: string;
  price: number;
  product_url: string;
  image_url: string;
  sold_count: number;
  search_keyword: string;
  scraped_at: string;
}

interface KeywordStats {
  keyword: string;
  count: number;
}

const Suppliers = () => {
  const { t } = useTranslation();
  const [suppliers, setSuppliers] = useState<Supplier1688[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [keywords, setKeywords] = useState<KeywordStats[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string>('');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    loadKeywords();
    loadSuppliers();
  }, []);

  const loadKeywords = async () => {
    try {
      const { data, error } = await supabase
        .from('suppliers_1688')
        .select('search_keyword');

      if (error) throw error;

      // Count by keyword
      const keywordCounts: Record<string, number> = {};
      data?.forEach((item: { search_keyword: string }) => {
        const kw = item.search_keyword || 'unknown';
        keywordCounts[kw] = (keywordCounts[kw] || 0) + 1;
      });

      const stats = Object.entries(keywordCounts).map(([keyword, count]) => ({
        keyword,
        count,
      })).sort((a, b) => b.count - a.count);

      setKeywords(stats);
      setTotalCount(data?.length || 0);
    } catch (error) {
      console.error('Failed to load keywords:', error);
    }
  };

  const loadSuppliers = async (keyword?: string, search?: string) => {
    setLoading(true);
    try {
      let query = supabase
        .from('suppliers_1688')
        .select('*')
        .order('price', { ascending: true })
        .limit(50);

      if (keyword) {
        query = query.eq('search_keyword', keyword);
      }

      if (search) {
        query = query.ilike('title', `%${search}%`);
      }

      const { data, error } = await query;

      if (error) throw error;
      setSuppliers(data || []);
    } catch (error) {
      console.error('Failed to load suppliers:', error);
      message.error('加载供应商数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeywordChange = (value: string) => {
    setSelectedKeyword(value);
    loadSuppliers(value, searchText);
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    loadSuppliers(selectedKeyword, value);
  };

  const columns = [
    {
      title: '图片',
      dataIndex: 'image_url',
      key: 'image',
      width: 80,
      render: (url: string) => (
        <Image
          src={url}
          alt="product"
          width={60}
          height={60}
          style={{ objectFit: 'cover', borderRadius: 4 }}
          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        />
      ),
    },
    {
      title: '产品名称',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      render: (text: string, record: Supplier1688) => (
        <a href={record.product_url} target="_blank" rel="noopener noreferrer">
          {text}
        </a>
      ),
    },
    {
      title: '类别',
      dataIndex: 'search_keyword',
      key: 'keyword',
      width: 100,
      render: (keyword: string) => <Tag color="blue">{keyword}</Tag>,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 100,
      sorter: (a: Supplier1688, b: Supplier1688) => a.price - b.price,
      render: (price: number) => (
        <Text strong style={{ color: '#f5222d' }}>¥{price.toFixed(2)}</Text>
      ),
    },
    {
      title: '建议零售价(AU$)',
      key: 'retail_price',
      width: 140,
      render: (_: unknown, record: Supplier1688) => {
        const auLow = (record.price * 0.21 * 3).toFixed(0);
        const auHigh = (record.price * 0.21 * 5).toFixed(0);
        return <Text type="success">${auLow} - ${auHigh}</Text>;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: Supplier1688) => (
        <Button
          type="link"
          icon={<LinkOutlined />}
          href={record.product_url}
          target="_blank"
        >
          查看
        </Button>
      ),
    },
  ];

  const top10Columns = [
    { title: '排名', dataIndex: 'rank', key: 'rank', width: 60, render: (rank: number) => <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#f5222d' : '#1890ff' }} /> },
    { title: '产品名称', dataIndex: 'title', key: 'title', render: (text: string, record: typeof TOP10_PRODUCTS[0]) => <a href={record.url} target="_blank" rel="noopener noreferrer">{text}</a> },
    { title: '类别', dataIndex: 'category', key: 'category', width: 100, render: (cat: string) => <Tag color="blue">{cat}</Tag> },
    { title: '采购价', dataIndex: 'price', key: 'price', width: 80, render: (price: number) => <Text strong style={{ color: '#f5222d' }}>¥{price}</Text> },
    { title: '建议零售价(AU$)', key: 'auPrice', width: 140, render: (_: unknown, record: typeof TOP10_PRODUCTS[0]) => <Text type="success">${record.auPriceLow} - ${record.auPriceHigh}</Text> },
    { title: '利润率', dataIndex: 'profitRate', key: 'profitRate', width: 80, render: (rate: string) => <Tag color="green">{rate}</Tag> },
    { title: '操作', key: 'action', width: 80, render: (_: unknown, record: typeof TOP10_PRODUCTS[0]) => <Button type="link" icon={<LinkOutlined />} href={record.url} target="_blank">采购</Button> },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <ShopOutlined /> 1688供应商数据库
      </Title>

      {/* TOP 10 Selection Report */}
      <Card
        style={{ marginBottom: 24, background: 'linear-gradient(135deg, #fff7e6 0%, #fff1f0 100%)' }}
        title={<span><TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />澳新市场 TOP 10 选品推荐 <Tag color="red"><FireOutlined /> 热门</Tag></span>}
      >
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">基于1688数据库224个产品，结合<Text strong>价格竞争力、跨境适配性、利润空间</Text>综合分析</Text>
        </div>
        <Table
          columns={top10Columns}
          dataSource={TOP10_PRODUCTS}
          rowKey="rank"
          pagination={false}
          size="small"
        />
        <div style={{ marginTop: 16, padding: 12, background: '#f6ffed', borderRadius: 4 }}>
          <Text strong>首批测试推荐：</Text>
          <Tag color="green" style={{ marginLeft: 8 }}>充电宝 - 刚需轻便</Tag>
          <Tag color="green">蓝牙耳机 - 高需求</Tag>
          <Tag color="green">太阳镜 - 300%+利润</Tag>
        </div>
      </Card>

      {/* Stats Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="供应商总数"
              value={totalCount}
              prefix={<ShopOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="产品类别"
              value={keywords.length}
              prefix={<SearchOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="最低价格"
              value={suppliers.length > 0 ? Math.min(...suppliers.map(s => s.price)) : 0}
              prefix={<DollarOutlined />}
              suffix="¥"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均价格"
              value={suppliers.length > 0 ? (suppliers.reduce((acc, s) => acc + s.price, 0) / suppliers.length).toFixed(1) : 0}
              prefix={<DollarOutlined />}
              suffix="¥"
            />
          </Card>
        </Col>
      </Row>

      {/* Filter Bar */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Select
            placeholder="选择类别"
            style={{ width: 200 }}
            allowClear
            onChange={handleKeywordChange}
            value={selectedKeyword || undefined}
          >
            {keywords.map(k => (
              <Select.Option key={k.keyword} value={k.keyword}>
                {k.keyword} ({k.count})
              </Select.Option>
            ))}
          </Select>
          <Search
            placeholder="搜索产品名称"
            style={{ width: 300 }}
            onSearch={handleSearch}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setSelectedKeyword('');
              setSearchText('');
              loadSuppliers();
            }}
          >
            重置
          </Button>
        </Space>
      </Card>

      {/* Suppliers Table */}
      <Card title={`供应商列表 (${suppliers.length})`}>
        <Table
          columns={columns}
          dataSource={suppliers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  );
};

export default Suppliers;
