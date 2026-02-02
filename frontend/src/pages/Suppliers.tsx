import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Input, Select, Image, Statistic, Space, Button, Typography, message, Collapse, Badge } from 'antd';
import { ShopOutlined, SearchOutlined, ReloadOutlined, DollarOutlined, LinkOutlined, TrophyOutlined, FireOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { supabase } from '../services/supabase';

const { Title, Text } = Typography;
const { Search } = Input;

// TOP 10 推荐选品数据 - 包含详细市场分析
const TOP10_PRODUCTS = [
  {
    rank: 1,
    title: '八爪鱼太阳能庭院灯(防水遥控)',
    category: '庭院监控',
    price: 22,
    auPriceLow: 14,
    auPriceHigh: 23,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/902544931709.html',
    rankReason: '综合评分最高：低成本+高需求+易运输',
    marketDemand: '⭐⭐⭐⭐⭐ 极高',
    targetAudience: '澳洲独栋房屋业主（占住宅70%+）',
    whyPopular: '澳洲家庭普遍有大庭院，太阳能产品环保且无需布线，DIY安装受欢迎。夏季日照长，太阳能效率高。',
    competition: '中等 - Amazon AU同类产品$25-50',
    seasonality: '全年销售，夏季(11-2月)旺季',
    keywords: 'solar garden light, outdoor security light, motion sensor light'
  },
  {
    rank: 2,
    title: '头戴式蓝牙耳机(降噪长续航)',
    category: '蓝牙耳机',
    price: 35,
    auPriceLow: 22,
    auPriceHigh: 37,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/878346774131.html',
    rankReason: '高需求品类+差异化卖点(降噪+长续航)',
    marketDemand: '⭐⭐⭐⭐⭐ 极高',
    targetAudience: '通勤族、远程办公者、游戏玩家',
    whyPopular: '澳洲通勤时间长(平均45分钟)，降噪耳机需求大。远程办公普及后，视频会议耳机需求激增。',
    competition: '高 - 但大牌价格$150+，平价市场有空间',
    seasonality: '全年稳定，圣诞季礼品需求上升',
    keywords: 'wireless headphones, noise cancelling, bluetooth headset'
  },
  {
    rank: 3,
    title: '20000mAh充电宝(自带线数显)',
    category: '充电宝',
    price: 11,
    auPriceLow: 7,
    auPriceHigh: 15,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/902558239373.html',
    rankReason: '刚需产品+超低成本+高复购率',
    marketDemand: '⭐⭐⭐⭐⭐ 极高',
    targetAudience: '户外爱好者、旅行者、学生、上班族',
    whyPopular: '澳洲户外活动盛行(露营、徒步)，充电宝是必备。自带线设计解决忘带线痛点，数显功能提升使用体验。',
    competition: '高 - 但自带线款式较少，差异化明显',
    seasonality: '全年稳定，假期旅游季需求上升',
    keywords: 'power bank, portable charger, battery pack'
  },
  {
    rank: 4,
    title: '迷你充电宝(四线便携)',
    category: '充电宝',
    price: 16,
    auPriceLow: 10,
    auPriceHigh: 17,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/943461513723.html',
    rankReason: '便携设计+多接口兼容+礼品属性',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: '女性用户、商务人士、礼品购买者',
    whyPopular: '四线设计兼容所有手机(iPhone/Android/Type-C)，迷你便携适合随身携带，是热门礼品选择。',
    competition: '中等 - 四线款市场少见',
    seasonality: '全年稳定，节日礼品季热销',
    keywords: 'mini power bank, slim portable charger, gift power bank'
  },
  {
    rank: 5,
    title: 'TPE双色瑜伽垫(6mm防滑)',
    category: '瑜伽垫',
    price: 15,
    auPriceLow: 9,
    auPriceHigh: 16,
    profitRate: '180%+',
    url: 'https://detail.1688.com/offer/604191338681.html',
    rankReason: '健身热潮+环保材质+高颜值设计',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: '瑜伽爱好者、健身人群、居家锻炼者',
    whyPopular: '澳洲健身文化浓厚，瑜伽参与率高。TPE环保材质符合当地环保意识，双色设计满足颜值需求。',
    competition: '中等 - 但环保材质是卖点',
    seasonality: '全年稳定，新年健身季(1-3月)旺季',
    keywords: 'yoga mat, exercise mat, eco friendly yoga mat, TPE mat'
  },
  {
    rank: 6,
    title: 'TWS蓝牙耳机(游戏触控)',
    category: '蓝牙耳机',
    price: 15,
    auPriceLow: 9,
    auPriceHigh: 16,
    profitRate: '180%+',
    url: 'https://detail.1688.com/offer/1007496887108.html',
    rankReason: '低价入门款+游戏功能+年轻用户',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: '学生、年轻游戏玩家、预算有限用户',
    whyPopular: '澳洲游戏市场活跃，TWS耳机是入门首选。触控操作现代感强，低延迟游戏模式是卖点。',
    competition: '高 - 但超低价位有优势',
    seasonality: '全年稳定，返校季(1-2月)热销',
    keywords: 'wireless earbuds, gaming earbuds, TWS earphones'
  },
  {
    rank: 7,
    title: 'AI翻译蓝牙耳机(开放式)',
    category: '蓝牙耳机',
    price: 40,
    auPriceLow: 25,
    auPriceHigh: 42,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/986395632592.html',
    rankReason: '创新功能+多元文化市场+高附加值',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: '移民群体、国际旅行者、商务人士',
    whyPopular: '澳洲是移民国家(30%海外出生)，多语言需求大。AI翻译功能实用，开放式设计舒适安全。',
    competition: '低 - 创新品类竞争少',
    seasonality: '全年稳定',
    keywords: 'translator earbuds, AI earphones, language translation headphones'
  },
  {
    rank: 8,
    title: 'ANC降噪蓝牙耳机(苹果适用)',
    category: '蓝牙耳机',
    price: 38,
    auPriceLow: 24,
    auPriceHigh: 40,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/918394204383.html',
    rankReason: 'iPhone用户基数大+ANC是刚需+性价比高',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: 'iPhone用户、苹果生态用户',
    whyPopular: '澳洲iPhone市场份额超50%，用户愿意购买兼容配件。AirPods Pro价格$400+，平价替代有市场。',
    competition: '中高 - 但价格优势明显',
    seasonality: '全年稳定，iPhone新品发布后需求上升',
    keywords: 'ANC earbuds, noise cancelling earbuds for iPhone, AirPods alternative'
  },
  {
    rank: 9,
    title: '运动骑行太阳镜(防紫外线)',
    category: '太阳镜',
    price: 3,
    auPriceLow: 5,
    auPriceHigh: 10,
    profitRate: '300%+',
    url: 'https://detail.1688.com/offer/649724946654.html',
    rankReason: '超低成本+超高利润+刚需品类',
    marketDemand: '⭐⭐⭐⭐⭐ 极高',
    targetAudience: '户外运动者、骑行爱好者、日常防晒需求',
    whyPopular: '澳洲紫外线全球最强，皮肤癌发病率高，防UV是刚需。户外运动文化盛行，骑行太阳镜需求大。',
    competition: '高 - 但成本极低利润空间大',
    seasonality: '夏季(11-2月)旺季，全年有需求',
    keywords: 'cycling sunglasses, sport sunglasses, UV protection glasses'
  },
  {
    rank: 10,
    title: '户外折叠野餐桌(便携轻量)',
    category: '野餐桌',
    price: 18,
    auPriceLow: 12,
    auPriceHigh: 20,
    profitRate: '200%+',
    url: 'https://detail.1688.com/offer/5926100527361.html',
    rankReason: '户外文化契合+高使用场景+差异化',
    marketDemand: '⭐⭐⭐⭐ 高',
    targetAudience: '露营爱好者、家庭野餐、户外活动者',
    whyPopular: '澳洲BBQ和野餐文化根深蒂固，周末户外活动是生活方式。折叠便携设计适合车载，轻量化是卖点。',
    competition: '中等 - 户外用品市场竞争分散',
    seasonality: '春夏旺季(9-3月)，秋冬淡季',
    keywords: 'folding picnic table, portable camping table, outdoor folding table'
  },
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

  const [expandedProduct, setExpandedProduct] = useState<number | null>(null);

  const renderProductCard = (product: typeof TOP10_PRODUCTS[0]) => (
    <Card
      key={product.rank}
      style={{
        marginBottom: 16,
        border: product.rank <= 3 ? '2px solid #f5222d' : '1px solid #d9d9d9',
        background: product.rank <= 3 ? '#fff7e6' : '#fff'
      }}
      hoverable
      onClick={() => setExpandedProduct(expandedProduct === product.rank ? null : product.rank)}
    >
      <Row gutter={16} align="middle">
        <Col span={1}>
          <Badge count={product.rank} style={{ backgroundColor: product.rank <= 3 ? '#f5222d' : '#1890ff', fontSize: 16 }} />
        </Col>
        <Col span={6}>
          <Text strong style={{ fontSize: 15 }}>{product.title}</Text>
          <br />
          <Tag color="blue">{product.category}</Tag>
          <Tag color="green">{product.profitRate}</Tag>
        </Col>
        <Col span={3}>
          <Text type="secondary">采购价</Text>
          <br />
          <Text strong style={{ color: '#f5222d', fontSize: 18 }}>¥{product.price}</Text>
        </Col>
        <Col span={4}>
          <Text type="secondary">建议零售价</Text>
          <br />
          <Text strong style={{ color: '#52c41a', fontSize: 16 }}>AU${product.auPriceLow}-${product.auPriceHigh}</Text>
        </Col>
        <Col span={4}>
          <Text type="secondary">市场需求</Text>
          <br />
          <Text>{product.marketDemand}</Text>
        </Col>
        <Col span={4}>
          <Text type="secondary">排名理由</Text>
          <br />
          <Text style={{ color: '#1890ff' }}>{product.rankReason}</Text>
        </Col>
        <Col span={2}>
          <Button type="primary" icon={<LinkOutlined />} href={product.url} target="_blank" onClick={(e) => e.stopPropagation()}>
            查看
          </Button>
        </Col>
      </Row>

      {expandedProduct === product.rank && (
        <div style={{ marginTop: 16, padding: 16, background: '#fafafa', borderRadius: 8 }}>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card size="small" title="🎯 目标客户" bordered={false}>
                <Text>{product.targetAudience}</Text>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="📊 竞争分析" bordered={false}>
                <Text>{product.competition}</Text>
              </Card>
            </Col>
            <Col span={24}>
              <Card size="small" title="💡 为什么在澳新市场有潜力？" bordered={false} style={{ background: '#e6f7ff' }}>
                <Text style={{ fontSize: 14 }}>{product.whyPopular}</Text>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="📅 季节性" bordered={false}>
                <Text>{product.seasonality}</Text>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="🔍 推荐关键词 (英文SEO)" bordered={false}>
                <Text code style={{ fontSize: 12 }}>{product.keywords}</Text>
              </Card>
            </Col>
          </Row>
        </div>
      )}
    </Card>
  );

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <ShopOutlined /> 1688供应商数据库
      </Title>

      {/* TOP 10 Selection Report */}
      <Card
        style={{ marginBottom: 24 }}
        title={<span><TrophyOutlined style={{ color: '#faad14', marginRight: 8 }} />澳新市场 TOP 10 选品推荐 <Tag color="red"><FireOutlined /> 热门</Tag></span>}
        extra={<Text type="secondary">点击卡片查看详细分析</Text>}
      >
        <div style={{ marginBottom: 16, padding: 12, background: 'linear-gradient(135deg, #e6f7ff 0%, #f6ffed 100%)', borderRadius: 8 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text strong>📊 数据来源：</Text>
              <Text>1688平台224个产品</Text>
            </Col>
            <Col span={8}>
              <Text strong>🎯 目标市场：</Text>
              <Text>澳大利亚 & 新西兰</Text>
            </Col>
            <Col span={8}>
              <Text strong>📈 分析维度：</Text>
              <Text>价格竞争力、市场需求、利润空间</Text>
            </Col>
          </Row>
        </div>

        <div style={{ marginBottom: 16 }}>
          <Text strong>首批测试推荐：</Text>
          <Tag color="green" style={{ marginLeft: 8 }}>充电宝 - 刚需轻便</Tag>
          <Tag color="green">蓝牙耳机 - 高需求</Tag>
          <Tag color="green">太阳镜 - 300%+利润</Tag>
        </div>

        {TOP10_PRODUCTS.map(product => renderProductCard(product))}
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
