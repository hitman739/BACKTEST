import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('query');

  if (!query) {
    return NextResponse.json({ error: 'Query parameter is required' }, { status: 400 });
  }

  const appId = process.env.EBAY_APP_ID || 'demo';
  const baseUrl = 'https://svcs.ebay.com/services/search/FindingService/v1';

  try {
    // Get sold items from eBay
    const response = await axios.get(baseUrl, {
      params: {
        'OPERATION-NAME': 'findCompletedItems',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': appId,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': query,
        'itemFilter(0).name': 'SoldItemsOnly',
        'itemFilter(0).value': 'true',
        'sortOrder': 'EndTimeSoonest',
        'paginationInput.entriesPerPage': '100',
      },
    });

    const data = response.data;

    if (!data.findCompletedItemsResponse?.[0]?.searchResult?.[0]?.item) {
      return NextResponse.json({
        items: [],
        summary: {
          count: 0,
          averagePrice: 0,
          minPrice: 0,
          maxPrice: 0,
        }
      });
    }

    const items = data.findCompletedItemsResponse[0].searchResult[0].item;

    // Process items and calculate statistics
    const processedItems = items
      .filter(item => item.sellingStatus?.[0]?.currentPrice?.[0]?.__value__)
      .map(item => ({
        id: item.itemId?.[0],
        title: item.title?.[0],
        price: parseFloat(item.sellingStatus[0].currentPrice[0].__value__),
        currency: item.sellingStatus[0].currentPrice[0]['@currencyId'],
        endTime: item.listingInfo?.[0]?.endTime?.[0],
        image: item.galleryURL?.[0] || item.pictureURLLarge?.[0],
        url: item.viewItemURL?.[0],
        condition: item.condition?.[0]?.conditionDisplayName?.[0] || 'N/A',
      }));

    // Calculate summary statistics
    const prices = processedItems.map(item => item.price);
    const summary = {
      count: processedItems.length,
      averagePrice: prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0,
      minPrice: prices.length > 0 ? Math.min(...prices) : 0,
      maxPrice: prices.length > 0 ? Math.max(...prices) : 0,
      currency: processedItems[0]?.currency || 'USD',
    };

    // Group by date for chart
    const priceByDate = processedItems.reduce((acc, item) => {
      const date = new Date(item.endTime).toISOString().split('T')[0];
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(item.price);
      return acc;
    }, {});

    const chartData = Object.entries(priceByDate)
      .map(([date, prices]) => ({
        date,
        averagePrice: prices.reduce((a, b) => a + b, 0) / prices.length,
        minPrice: Math.min(...prices),
        maxPrice: Math.max(...prices),
        count: prices.length,
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    return NextResponse.json({
      items: processedItems.slice(0, 20), // Return top 20 most recent
      summary,
      chartData,
    });

  } catch (error) {
    console.error('eBay API Error:', error.response?.data || error.message);
    return NextResponse.json(
      { error: 'Failed to fetch data from eBay', details: error.message },
      { status: 500 }
    );
  }
}
